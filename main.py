import os
import pygame
import requests
import threading
import time
import logging
from yandex_music import Client
from io import BytesIO
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# Определяем путь к директории, в которой будет храниться токен
token_dir = "C:/Program Files/UnofficialYandexPlayer"

# Создаём директорию, если её нет
if not os.path.exists(token_dir):
    os.makedirs(token_dir)

# Окно для ввода токена при первом запуске
token_file = os.path.join(token_dir, "token.txt")
if os.path.exists(token_file):
    with open(token_file, "r") as file:
        token = file.read().strip()
else:
    root = tk.Tk()
    root.geometry("300x100")
    root.title("Enter Yandex Music Token")
    label = ttk.Label(root, text="Please enter your Yandex Music token:")
    label.pack(pady=10)
    token_entry = ttk.Entry(root)
    token_entry.pack()

    def save_token():
        global token
        token = token_entry.get().strip()
        with open(token_file, "w") as file:
            file.write(token)
        root.destroy()

    save_button = ttk.Button(root, text="Save Token", command=save_token)
    save_button.pack()

    root.mainloop()

# Инициализация Pygame
pygame.init()
pygame.mixer.init()
music_player = pygame.mixer.music

# Инициализация логгирования
log_file = "music_player.log"
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Получение списка треков
client = Client(token).init()
tracks = client.users_likes_tracks()

# Индекс текущего трека
current_track_index = 0

# Состояние воспроизведения
playing = False

# Автоматическое переключение треков
auto_play_enabled = True

# Функции
def next_track_index(current_index):
    """
    Возвращает индекс следующего трека в зависимости от режима автоплея.
    """
    if auto_play_enabled:
        return (current_index + 1) % len(tracks)
    else:
        return current_index

def log_action(action):
    """
    Логирует действие.
    """
    logging.info(action)

def load_track(index):
    """
    Загружает трек, скачивает его и проигрывает.
    """
    global current_track_index
    current_track_index = next_track_index(index)

    track = tracks[current_track_index].fetch_track()
    download_info = track.get_download_info(get_direct_links=True)

    direct_link = download_info[0].direct_link
    track_name = "{}.mp3".format(track.title.lower().replace(" ", "_"))

    response = requests.get(direct_link, stream=True)
    audio_content = BytesIO(response.content)

    music_player.load(audio_content)
    music_player.set_volume(1.0)
    music_player.play()

    label.config(text=f"Now playing: {track.title}")
    global playing
    playing = True

    log_action(f"Loaded track: {track.title}")

def play_music(time=0):
    """
    Запускает воспроизведение.
    """
    global playing
    if not playing:
        music_player.play()
        playing = True
        log_action("Started playback")
    elif time > 0:
        pygame.time.delay(time * 1000)
        play_music()

def stop_music(time=0):
    """
    Останавливает воспроизведение.
    """
    global playing
    if playing:
        music_player.stop()
        playing = False
        if time > 0:
            pygame.time.delay(time * 1000)
        log_action("Stopped playback")

def play_next_track():
    """
    Проигрывает следующий трек.
    """
    stop_music(1)
    load_track(current_track_index + 1)
    play_music(1)
    log_action("Next track")

def play_previous_track():
    """
    Проигрывает предыдущий трек.
    """
    stop_music(1)
    load_track(current_track_index - 1)
    play_music(1)
    log_action("Previous track")

def toggle_auto_play():
    """
    Включает/выключает режим автоплея.
    """
    global auto_play_enabled
    auto_play_enabled = not auto_play_enabled
    auto_play_button.config(text="Auto Play: {}".format("On" if auto_play_enabled else "Off"))
    log_action("Auto Play: {}".format("On" if auto_play_enabled else "Off"))

def auto_play():
    """
    Автоматически переключает треки.
    """
    global current_track_index
    while True:
        if auto_play_enabled and not pygame.mixer.music.get_busy():
            next_index = next_track_index(current_track_index)
            if next_index != current_track_index:
                load_track(next_index)
                play_music(1)
        time.sleep(10)

# Создание потока для автоматического переключения
auto_play_thread = threading.Thread(target=auto_play)
auto_play_thread.daemon = True
auto_play_thread.start()

# Графический интерфейс
root = tk.Tk()
root.geometry("400x400")
root.title("Music Player")
root.configure(bg="black")

# Надпись с названием трека
label = ttk.Label(root, text="", foreground="white", background="black")
label.pack(pady=10)

# Кнопки управления
play_button = ttk.Button(root, text="Play", command=lambda: play_music(1))
play_button.pack()

stop_button = ttk.Button(root, text="Stop", command=lambda: stop_music(1))
stop_button.pack()

previous_button = ttk.Button(root, text="Previous", command=play_previous_track)
previous_button.pack()

next_button = ttk.Button(root, text="Next", command=play_next_track)
next_button.pack()

auto_play_button = ttk.Button(root, text="Auto Play: On", command=toggle_auto_play)
auto_play_button.pack()

# Фиксируем размер окна
root.resizable(False, False)

# Загружаем первый трек
load_track(current_track_index)

root.mainloop()

# Освобождение ресурсов Pygame
pygame.mixer.quit()
pygame.quit()