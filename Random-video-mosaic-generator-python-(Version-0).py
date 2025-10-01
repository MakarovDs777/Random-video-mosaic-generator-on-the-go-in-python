import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import pygame
from threading import Thread
from PIL import Image, ImageTk
from moviepy.editor import VideoFileClip
import random
from pydub import AudioSegment
import time
import tempfile
import os
import cv2

class AudioMosaic:
    def __init__(self):
        self.segments = []
        self.sample_rate = 0
        self.is_playing = False
        pygame.mixer.init()

    def convert_audio_to_segments(self, audio, segment_duration_ms=500):
        self.segments = []
        current_time = 0

        while current_time < len(audio):
            segment = audio[current_time:current_time + segment_duration_ms]
            self.segments.append(segment.raw_data)
            current_time += segment_duration_ms
        
        self.sample_rate = audio.frame_rate

    def mix_audio_segments(self):
        random.shuffle(self.segments)
        return b''.join(self.segments)

    def play_audio(self):
        self.is_playing = True
        while self.is_playing:
            shuffled_audio = self.mix_audio_segments()
            sound_array = np.frombuffer(shuffled_audio, dtype=np.int16)
            pygame.mixer.Sound(buffer=sound_array).play()

            # Даем время на воспроизведение сегментов
            time.sleep(len(shuffled_audio) / (self.sample_rate * 2))

    def stop_audio(self):
        self.is_playing = False
        pygame.mixer.stop()

video_clips = []
audio_mosaic = AudioMosaic()

current_frame_index = 0
move_speed = 1  # Скорость перемещения

def load_videos():
    global video_clips
    video_paths = filedialog.askopenfilenames(title="Выберите видео файлы", filetypes=[("Video files", "*.mp4;*.avi;*.mov")])
    if video_paths:
        for video_path in video_paths:
            video_clip = VideoFileClip(video_path)
            video_clips.append((video_path, video_clip))
            video_listbox.insert(tk.END, video_path)

def shuffle_frame(frame, iterations=6):
    plitkorez = 6  # Количество плиток по каждой оси
    height, width, _ = frame.shape
    h, w = height // plitkorez, width // plitkorez
    
    tiles = []
    for i in range(plitkorez):
        for j in range(plitkorez):
            y_start = i * h
            y_end = (i + 1) * h if (i + 1) * h < height else height
            x_start = j * w
            x_end = (j + 1) * w if (j + 1) * w < width else width
            tiles.append(frame[y_start:y_end, x_start:x_end])

    random.shuffle(tiles)

    reshuffled_frame = []
    for i in range(plitkorez):
        reshuffled_frame.append(np.hstack(tiles[i * plitkorez:(i + 1) * plitkorez]))

    return np.vstack(reshuffled_frame)

def display_frame(frame_index):
    global current_frame_index
    if video_clips:
        video_clip = video_clips[current_frame_index][1]
        if frame_index >= video_clip.duration * video_clip.fps:  # Проверка на границу
            frame_index = 0
        frame = video_clip.get_frame(frame_index / video_clip.fps)
        frame_array = np.array(Image.fromarray(frame).resize((640, 480), Image.LANCZOS))

        # Перемешиваем плитки
        shuffled_frame = shuffle_frame(frame_array)

        # Применяем размытие
        blurred_frame = cv2.GaussianBlur(shuffled_frame, (41, 41), 0)

        # Преобразуем в изображение для tkinter
        blurred_frame_photo = ImageTk.PhotoImage(Image.fromarray(blurred_frame))

        # Отображаем изображение
        canvas.create_image(0, 0, anchor=tk.NW, image=blurred_frame_photo)
        canvas.image = blurred_frame_photo

def move_camera(direction):
    global current_frame_index
    if direction == "F":  # Вперед
        current_frame_index += move_speed
    elif direction == "B":  # Назад
        current_frame_index -= move_speed
    elif direction == "L":  # Сменить на предыдущее видео
        current_frame_index = max(0, current_frame_index - 1)
    elif direction == "R":  # Сменить на следующее видео
        current_frame_index = min(len(video_clips) - 1, current_frame_index + 1)

    # Проверяем, чтобы индекс не выходил за пределы
    if current_frame_index < 0:
        current_frame_index = 0
    elif current_frame_index >= len(video_clips):
        current_frame_index = len(video_clips) - 1

    display_frame(current_frame_index)

def on_key_press(event):
    key = event.keysym
    if key == 'w':
        move_camera("F")
    elif key == 's':
        move_camera("B")
    elif key == 'a':
        move_camera("L")
    elif key == 'd':
        move_camera("R")

def start_video():
    global video_clips
    if not video_clips:
        messagebox.showwarning("Предупреждение", "Выберите видео файлы сначала.")
        return

    audio_segments = []
    for video_path, video_clip in video_clips:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
            audio_path = temp_audio_file.name
            video_clip.audio.write_audiofile(audio_path)
            audio_segment = AudioSegment.from_file(audio_path)

            audio_segments.append(audio_segment)

        os.remove(audio_path)  # Удаляем файл после использования

    combined_audio = sum(audio_segments)
    audio_mosaic.convert_audio_to_segments(combined_audio)
    Thread(target=audio_mosaic.play_audio, daemon=True).start()  
    display_frame(current_frame_index)  # Начальное отображение кадра

# Создание графического интерфейса
root = tk.Tk()
root.title("Генератор случайного видео")

canvas = tk.Canvas(root, width=640, height=480)
canvas.pack()

video_listbox = tk.Listbox(root, width=80, height=10)
video_listbox.pack()

select_button = tk.Button(root, text="Выбрать видео", command=load_videos)
select_button.pack()

start_button = tk.Button(root, text="Старт видео", command=start_video)
start_button.pack()

root.bind("<KeyPress>", on_key_press)  # Привязываем обработчик к событиям клавиш

# Запустить основной цикл интерфейса
root.mainloop()
