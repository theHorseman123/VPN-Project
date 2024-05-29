import tkinter as tk
from tkinter import messagebox
import pygame
import os

# Initialize pygame mixer
pygame.mixer.init()

# Path to the Doom theme music file
# Make sure you have the Doom theme music file (doom_theme.mp3) in the same directory as your script
music_file = "doom_theme.mp3"

# Function to play music
def play_music():
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.play(-1)  # -1 means loop the music indefinitely
        messagebox.showinfo("Music", "Doom theme music is now playing on repeat!")

# Function to stop music
def stop_music():
    pygame.mixer.music.stop()
    messagebox.showinfo("Music", "Doom theme music has been stopped!")

# Setting up the Tkinter window
root = tk.Tk()
root.title("Doom Theme Music Player")
root.geometry("300x200")

# Adding the play button
play_button = tk.Button(root, text="Play Doom Theme", command=play_music, bg="green", fg="white", font=("Helvetica", 14))
play_button.pack(pady=20)

# Adding the stop button
stop_button = tk.Button(root, text="Stop Music", command=stop_music, bg="red", fg="white", font=("Helvetica", 14))
stop_button.pack(pady=20)

# Run the Tkinter event loop
root.mainloop()