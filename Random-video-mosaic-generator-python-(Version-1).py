import tkinter as tk
from tkinter import filedialog
import numpy as np
import pygame
from threading import Thread
from PIL import Image, ImageTk
from moviepy.editor import VideoFileClip
import random
import cv2

video_clip = None
audio_clip = None

def load_video(video_path):
    global video_clip, audio_clip
    video_clip = VideoFileClip(video_path)
    audio_clip = video_clip.audio

def play_sound():
    global audio_clip
    sample_rate = 44100
    pygame.mixer.init(frequency=sample_rate, size=-16, channels=1)

    while True:
        start_time = random.uniform(0, audio_clip.duration - 1)
        end_time = min(start_time + 1, audio_clip.duration)  # 1-секундный фрагмент

        audio_segment = audio_clip.subclip(start_time, end_time)
        audio_segment_array = audio_segment.to_soundarray(fps=sample_rate)

        sound = (audio_segment_array * 32767).astype(np.int16)
        pygame.mixer.Sound(buffer=sound.tobytes()).play()

        pygame.time.delay(1000)  # Пауза на 1 секунду перед воспроизведением следующего

def shuffle_frame(frame):
    height, width, _ = frame.shape

    # Убедимся, что при делении на 2, мы корректно разбиваем на 4 плитки
    h, w = height // 2, width // 2

    # Переписываем плитки, чтобы гарантировать, что мы имеем 4 плитки
    tiles = [
        frame[0:h, 0:w],        # Верхняя левая плитка
        frame[0:h, w:width],    # Верхняя правая плитка
        frame[h:height, 0:w],   # Нижняя левая плитка
        frame[h:height, w:width] # Нижняя правая плитка
    ]

    # Перемешивание плиток
    random.shuffle(tiles)

    # Собираем плитки обратно в одно изображение
    shuffled_frame = np.vstack((np.hstack((tiles[0], tiles[1])), np.hstack((tiles[2], tiles[3]))))

    return shuffled_frame

def display_random_frame():
    if video_clip:
        start_time = random.uniform(0, video_clip.duration - 1)
        frame = video_clip.get_frame(start_time)

        # Преобразование массива в изображение PIL
        frame_image = Image.fromarray(frame)

        # Изменение размера изображения, чтобы оно подходило под canvas
        frame_image = frame_image.resize((640, 480), Image.LANCZOS)  # Масштабируем изображение с использованием LANCZOS

        # Преобразование изображения PIL в массив numpy
        frame_array = np.array(frame_image)

        # Перемешивание кадра
        shuffled_frame = shuffle_frame(frame_array)

        # Преобразование массива numpy обратно в изображение PIL
        shuffled_frame_image = Image.fromarray(shuffled_frame)

        # Изменение размера изображения, чтобы оно подходило под canvas
        shuffled_frame_image = shuffled_frame_image.resize((640, 480), Image.LANCZOS)  # Масштабируем изображение с использованием LANCZOS

        # Преобразование изображения PIL в изображение PhotoImage
        shuffled_frame_photo = ImageTk.PhotoImage(shuffled_frame_image)

        # Обновление canvas с новым изображением
        canvas.create_image(0, 0, anchor=tk.NW, image=shuffled_frame_photo)
        canvas.image = shuffled_frame_photo  # Сохранение ссылки на изображение, чтобы избежать сборки мусора

    # Запланировать обновление через 1000 мс (1 секунда)
    canvas.after(1000, display_random_frame)

def start_audio_and_video(video_path):
    load_video(video_path)
    Thread(target=play_sound, daemon=True).start()  # Запуск звука в отдельном потоке
    display_random_frame()  # Запуск отображения случайных кадров

def select_video():
    file_path = filedialog.askopenfilename(title="Выберите видео файл")  
    if file_path:
        start_audio_and_video(file_path)

# Создание графического интерфейса
root = tk.Tk()
root.title("Random EVP Video Generator")

canvas = tk.Canvas(root, width=640, height=480)
canvas.pack()

select_button = tk.Button(root, text="Выбрать видео", command=select_video)
select_button.pack()

# Запустить основной цикл интерфейса
root.mainloop()
