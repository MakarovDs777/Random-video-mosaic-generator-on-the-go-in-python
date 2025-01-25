import tkinter as tk
from tkinter import filedialog
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

video_clip = None
audio_mosaic = AudioMosaic()

def load_video(video_path):
    global video_clip
    video_clip = VideoFileClip(video_path)

def shuffle_frame(frame, iterations=1):
    plitkorez = 2
    height, width, _ = frame.shape
    h, w = height // (plitkorez ** iterations), width // (plitkorez ** iterations)
    # Создаем плитки на основании итераций
    tiles = []
    for i in range(plitkorez ** iterations):
        for j in range(plitkorez ** iterations):
            y_start = i * h
            y_end = (i + 1) * h if (i + 1) * h < height else height
            x_start = j * w
            x_end = (j + 1) * w if (j + 1) * w < width else width
            tiles.append(frame[y_start:y_end, x_start:x_end])

    random.shuffle(tiles)
    
    # Соединяем плитки обратно в одно изображение
    reshuffled_frame = []
    for i in range(plitkorez ** iterations):
        reshuffled_frame.append(np.hstack(tiles[i * (plitkorez ** iterations):(i + 1) * (plitkorez ** iterations)]))

    return np.vstack(reshuffled_frame)

# Обновите вызов функции в display_random_frame:
def display_random_frame():
    if video_clip:
        start_time = random.uniform(0, video_clip.duration - 1)
        frame = video_clip.get_frame(start_time)
        frame_array = np.array(Image.fromarray(frame).resize((640, 480), Image.LANCZOS))
        iterations = 6  # Установите количество итераций, здесь для порезок на плитки
        shuffled_frame = shuffle_frame(frame_array, iterations)
        shuffled_frame_photo = ImageTk.PhotoImage(Image.fromarray(shuffled_frame))

        canvas.create_image(0, 0, anchor=tk.NW, image=shuffled_frame_photo)
        canvas.image = shuffled_frame_photo

    canvas.after(1000, display_random_frame)

def start_video():
    video_path = filedialog.askopenfilename(title="Выберите видео файл")
    if video_path:
        load_video(video_path)
        
        # Создаем временный файл для сохранения аудио
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
            audio_path = temp_audio_file.name
            video_clip.audio.write_audiofile(audio_path)

        # Загружаем сохраненное аудио в AudioSegment
        audio_segment = AudioSegment.from_file(audio_path)

        audio_mosaic.convert_audio_to_segments(audio_segment)  # Преобразование аудио в сегменты
        Thread(target=audio_mosaic.play_audio, daemon=True).start()  # Запуск аудио в отдельном потоке
        display_random_frame()  # Запуск отображения случайных кадров

        # Удаляем временный аудиофайл
        os.remove(audio_path)

# Создание графического интерфейса
root = tk.Tk()
root.title("Генератор случайного видео")

canvas = tk.Canvas(root, width=640, height=480)
canvas.pack()

select_button = tk.Button(root, text="Выбрать видео", command=start_video)
select_button.pack()

# Запустить основной цикл интерфейса
root.mainloop()
