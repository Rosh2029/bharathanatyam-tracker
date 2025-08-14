import os
import sys
import csv
import random
import tkinter as tk
from tkinter import ttk, messagebox
import pygame

# ---------------------------
# Paths that work in a .py OR a PyInstaller .exe
# ---------------------------
def app_base_dir() -> str:
    if getattr(sys, "frozen", False):          # running from .exe
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.dirname(__file__))

BASE_DIR = app_base_dir()
MUSIC_DIR = os.path.join(BASE_DIR, "music")    # expect music/ next to .py or .exe
CSV_PATH  = os.path.join(BASE_DIR, "practice_log.csv")

# ---------------------------
# Audio init (non-blocking)
# ---------------------------
pygame.mixer.init()

# ---------------------------
# Data
# ---------------------------
adavus_list = [
    "Tatta Adavu", "Natta Adavu", "Visharu Adavu",
    "Tatti Mettu Adavu", "Kuditta Mettu Adavu",
    "Sarikkal Adavu", "Teermanam Adavu"
]

items_list = [
    "Mishra Alarippu",
    "Jathiswaram 1", "Jathiswaram 2", "Jathiswaram 3",
    "Varnam", "Padam", "Tillana"
]

# ---------------------------
# Helpers
# ---------------------------
def ensure_csv():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["Date", "Category", "Name", "Duration (min)", "Notes"])

def normalize(s: str) -> str:
    # compare names sans spaces, hyphens, underscores, punctuation; case-insensitive
    return "".join(ch for ch in s.lower() if ch.isalnum())

def find_matches(folder: str, query: str):
    """Return list of full paths for audio files in folder that match query (forgiving)."""
    matches = []
    if not os.path.isdir(folder):
        return matches
    q = normalize(query)
    for fn in os.listdir(folder):
        p = os.path.join(folder, fn)
        if not os.path.isfile(p):
            continue
        base, ext = os.path.splitext(fn)
        if ext.lower() not in (".mp3", ".wav", ".ogg"):
            continue
        if q in normalize(base):   # partial OK
            matches.append(p)
    return matches

# ---------------------------
# GUI callbacks
# ---------------------------
def update_steps(*_):
    if category_var.get() == "Adavus":
        step_combo["values"] = adavus_list
    else:
        step_combo["values"] = items_list
    step_var.set("")

def play_music():
    stop_music()  # stop anything already playing

    category = category_var.get().strip()
    name = step_var.get().strip()
    if not category or not name:
        messagebox.showerror("Error", "Please select Category and Step/Item.")
        return

    # Choose folder by category
    folder = os.path.join(MUSIC_DIR, "adavus" if category == "Adavus" else "items")

    if category == "Adavus":
        # Keep Adavus simple: prefer exact normalized match; still forgiving
        candidates = find_matches(folder, name)
        if not candidates:
            messagebox.showerror(
                "Error",
                f"Music for '{name}' not found.\nLooked in:\n{folder}\n\n"
                f"Tip: place a file like '{name.lower().replace(' ', '_')}.mp3'."
            )
            return
        track = candidates[0]     # first match
    else:
        # Items can have multiple versions → pick one at random
        candidates = find_matches(folder, name)
        if not candidates:
            messagebox.showerror(
                "Error",
                f"Music for '{name}' not found.\nLooked in:\n{folder}\n\n"
                "You can name files flexibly, e.g. 'jathiswaram 1.mp3', "
                "'JATHISWARAM-1.wav', 'jathiswaram1.ogg'."
            )
            return
        track = random.choice(candidates)

    try:
        pygame.mixer.music.load(track)
        pygame.mixer.music.play()   # async; UI stays responsive
        now_playing_var.set(f"Now playing: {os.path.basename(track)}")
    except Exception as e:
        messagebox.showerror("Error", f"Could not play audio:\n{track}\n\n{e}")

def stop_music():
    pygame.mixer.music.stop()
    now_playing_var.set("")

def save_practice():
    ensure_csv()
    date = tk.StringVar()
    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d")

    category = category_var.get().strip()
    name = step_var.get().strip()
    duration = duration_var.get().strip()
    notes = notes_var.get().strip()

    if not category or not name or not duration:
        messagebox.showerror("Error", "Fill Category, Step/Item and Duration.")
        return

    try:
        int(duration)
    except ValueError:
        messagebox.showerror("Error", "Duration must be a number (minutes).")
        return

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([date, category, name, duration, notes])

    messagebox.showinfo("Saved", f"Saved practice for {name}.")
    duration_var.set("")
    notes_var.set("")

# ---------------------------
# GUI
# ---------------------------
root = tk.Tk()
root.title("Bharatanatyam Practice Tracker")
root.geometry("380x360")

category_var = tk.StringVar(value="Adavus")
step_var = tk.StringVar()
duration_var = tk.StringVar()
notes_var = tk.StringVar()
now_playing_var = tk.StringVar()

ttk.Label(root, text="Category").pack(pady=4)
category_combo = ttk.Combobox(root, textvariable=category_var, values=["Adavus", "Items"], state="readonly")
category_combo.pack()
category_var.trace_add("write", update_steps)

ttk.Label(root, text="Step / Item").pack(pady=4)
step_combo = ttk.Combobox(root, textvariable=step_var, values=adavus_list, state="readonly")
step_combo.pack()

ttk.Label(root, text="Duration (minutes)").pack(pady=4)
ttk.Entry(root, textvariable=duration_var).pack()

ttk.Label(root, text="Notes (optional)").pack(pady=4)
ttk.Entry(root, textvariable=notes_var).pack()

ttk.Button(root, text="Play Music", command=play_music).pack(pady=6)
ttk.Button(root, text="Stop Music", command=stop_music).pack(pady=2)
ttk.Button(root, text="Save Practice", command=save_practice).pack(pady=6)

ttk.Label(root, textvariable=now_playing_var, foreground="green").pack(pady=6)

root.mainloop()
