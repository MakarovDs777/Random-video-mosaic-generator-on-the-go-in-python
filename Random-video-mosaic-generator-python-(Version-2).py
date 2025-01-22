import tkinter as tk
from tkinter import filedialog
import numpy as np
import pygame
from threading import Thread
from PIL import Image, ImageTk
from moviepy.editor import VideoFileClip
import random
from pydub import AudioSegment
import time

class AudioMosaic:
    def __init__(self):
        self.segments = []
        self.sample_rate = 0
        self.is_playing = False
        pygame.mixer.init()  # Инициализация pygame mixer при создании объекта

    def convert_audio_to_segments(self, path, segment_duration_ms=500):
        audio = AudioSegment.from_file(path)  # Загружаем аудиофайл
        self.segments = []
        current_time = 0

        while current_time < len(audio):
            segment = audio[current_time:current_time + segment_duration_ms]  # Получаем кусок аудио
            self.segments.append(segment.raw_data)  # Добавляем сырье в список сегментов
            current_time += segment_duration_ms  # Обновляем текущее время
        
        self.sample_rate = audio.frame_rate  # Сохраняем частоту дискретизации

    def mix_audio_segments(self):
        random.shuffle(self.segments)  # Перемешиваем сегменты
        return b''.join(self.segments)  # Соединяем сегменты обратно в один поток байтов

    def play_audio(self):
        self.is_playing = True
        while self.is_playing:
            shuffled_audio = self.mix_audio_segments()  # Перемешиваем аудио каждый раз
            
            # Преобразование байтов в массив NumPy и создание звука
            sound_array = np.frombuffer(shuffled_audio, dtype=np.int16)
            pygame.mixer.Sound(buffer=sound_array).play()

            # Даем время на воспроизведение сегментов
            time.sleep(len(shuffled_audio) / (self.sample_rate * 2))  # Подсчет времени в секунды

    def stop_audio(self):
        self.is_playing = False  # Устанавливаем флаг в False
        pygame.mixer.stop()  # Останавливаем воспроизведение музыки

video_clip = None
audio_mosaic = AudioMosaic()
video_playing = False
last_shuffled_frame = None

def load_video(video_path):
    global video_clip
    video_clip = VideoFileClip(video_path)

def shuffle_frame(frame):
    height, width, _ = frame.shape
    h, w = height // 2, width // 2

    tiles = [
        frame[0:h, 0:w],
        frame[0:h, w:width],
        frame[h:height, 0:w],
        frame[h:height, w:width]
    ]

    random.shuffle(tiles)

    shuffled_frame = np.vstack((np.hstack((tiles[0], tiles[1])), np.hstack((tiles[2], tiles[3]))))

    return shuffled_frame

def display_random_frame():
    global last_shuffled_frame
    if video_clip and video_playing:
        start_time = random.uniform(0, video_clip.duration - 1)
        frame = video_clip.get_frame(start_time)
        shuffled_frame = shuffle_frame(frame)  # Перемешиваем кадр
        last_shuffled_frame = shuffled_frame  # Сохраняем перемешанный кадр
        frame_array = np.array(Image.fromarray(shuffled_frame).resize((640, 480), Image.LANCZOS))
        shuffled_frame_photo = ImageTk.PhotoImage(Image.fromarray(frame_array))

        canvas.create_image(0, 0, anchor=tk.NW, image=shuffled_frame_photo)
        canvas.image = shuffled_frame_photo

    canvas.after(1000, display_random_frame)

def start_audio_mosaic():
    audio_file_path = filedialog.askopenfilename(
        title="Выберите аудио файл", 
        filetypes=[("Audio Files", "*.wav;*.mp3;*.ogg;*.flac")]
    )
    
    if audio_file_path:
        audio_mosaic.convert_audio_to_segments(audio_file_path)  # Получаем сегменты состояния
        Thread(target=audio_mosaic.play_audio, daemon=True).start()  # Запуск воспроизведения перемешанного аудио

def start_video():
    global video_playing
    video_path = filedialog.askopenfilename(title="Выберите видео файл")
    if video_path:
        load_video(video_path)
        video_playing = True
        display_random_frame()  # Запуск отображения случайных кадров

def stop_video():
    global video_playing
    video_playing = False
    
    # Отображаем последний перемешанный кадр
    if last_shuffled_frame is not None:
        frame_array = np.array(Image.fromarray(last_shuffled_frame).resize((640, 480), Image.LANCZOS))
        last_frame_photo = ImageTk.PhotoImage(Image.fromarray(frame_array))
        canvas.create_image(0, 0, anchor=tk.NW, image=last_frame_photo)
        canvas.image = last_frame_photo  # Чтобы предотвратить сборку мусора

# Создание графического интерфейса
root = tk.Tk()
root.title("Генератор случайного видео и аудио")

canvas = tk.Canvas(root, width=640, height=480)
canvas.pack()

select_video_button = tk.Button(root, text="Выбрать видео", command=start_video)
select_video_button.pack()

select_audio_button = tk.Button(root, text="Выбрать аудио", command=start_audio_mosaic)
select_audio_button.pack()

stop_audio_button = tk.Button(root, text="Стоп аудио", command=audio_mosaic.stop_audio)
stop_audio_button.pack()

stop_video_button = tk.Button(root, text="Стоп видео", command=stop_video)
stop_video_button.pack()

# Запустить основной цикл интерфейса
root.mainloop()
