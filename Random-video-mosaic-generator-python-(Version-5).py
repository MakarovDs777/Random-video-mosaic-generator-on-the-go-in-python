import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import pygame
from threading import Thread
from PIL import Image, ImageTk
from moviepy.editor import VideoFileClip
import random
from pydub import AudioSegment
import tempfile
import os
import time
import cv2  # Импортируем OpenCV

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

def load_videos():
    global video_clips
    video_paths = filedialog.askopenfilenames(title="Выберите видео файлы", filetypes=[("Video files", "*.mp4;*.avi;*.mov")])
    if video_paths:
        for video_path in video_paths:
            video_clip = VideoFileClip(video_path)
            video_clips.append((video_path, video_clip))
            video_listbox.insert(tk.END, video_path)

def shuffle_frame(frame, iterations=6):
    plitkorez = 2
    height, width, _ = frame.shape
    h, w = height // (plitkorez ** iterations), width // (plitkorez ** iterations)
    
    tiles = []
    for i in range(plitkorez ** iterations):
        for j in range(plitkorez ** iterations):
            y_start = i * h
            y_end = (i + 1) * h if (i + 1) * h < height else height
            x_start = j * w
            x_end = (j + 1) * w if (j + 1) * w < width else width
            tiles.append(frame[y_start:y_end, x_start:x_end])

    random.shuffle(tiles)

    reshuffled_frame = []
    for i in range(plitkorez ** iterations):
        reshuffled_frame.append(np.hstack(tiles[i * (plitkorez ** iterations):(i + 1) * (plitkorez ** iterations)]))

    return np.vstack(reshuffled_frame)

def blur_frame(frame, blur_strength=41):  # Размываем весь кадр
    return cv2.GaussianBlur(frame, (blur_strength, blur_strength), 0)

def display_random_frame():
    if video_clips:
        video_clip = random.choice(video_clips)[1]
        start_time = random.uniform(0, video_clip.duration - 1)
        frame = video_clip.get_frame(start_time)
        frame_array = np.array(Image.fromarray(frame).resize((640, 480), Image.LANCZOS))
        
        # Перемешиваем плитки
        shuffled_frame = shuffle_frame(frame_array)

        # Применяем размытие
        blurred_frame = blur_frame(shuffled_frame)

        # Преобразуем в изображение для tkinter
        blurred_frame_photo = ImageTk.PhotoImage(Image.fromarray(blurred_frame))

        # Отображаем изображение
        canvas.create_image(0, 0, anchor=tk.NW, image=blurred_frame_photo)
        canvas.image = blurred_frame_photo

    canvas.after(1000, display_random_frame)

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
    display_random_frame()  

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

# Запустить основной цикл интерфейса
root.mainloop()
