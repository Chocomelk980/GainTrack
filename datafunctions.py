# Import necessary modules for CSV handling, file operations, date, and GUI messages
import csv
import json
import os
from datetime import date
from tkinter import messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "logs.csv")
SESSION_LOG_FILE = os.path.join(BASE_DIR, "session_logs.csv")
FIELDNAMES = ['Date', 'Food', 'Amount', 'Protein']
USERS_FILE = os.path.join(BASE_DIR, "users.csv")
STATE_FILE = os.path.join(BASE_DIR, "current_profile.json")

# Ginagamit ito para ipakitang from CSV nanggagaling ang list ng pagkain (Food -> protein per 100g)
def load_foods():
    foods = {}
    try:
        path = os.path.join(BASE_DIR, "foods.csv")
        with open(path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                foods[row['Food']] = float(row['Protein_per_100g'])
    except FileNotFoundError:
        messagebox.showerror("Error", "foods.csv not found!")
    return foods


# Dinodoble sa history at session files ang mga nalog na pagkain
def add_log(food, amount, protein):
    row = {'Date': str(date.today()), 'Food': food, 'Amount': amount, 'Protein': protein}
    _append_log(LOG_FILE, row)
    _append_log(SESSION_LOG_FILE, row)


# Kapag kailangan ipakita ang kabuuang intake ngayong araw, dito namin kinukuha (session muna bago full history)
def total_today():
    target_file = SESSION_LOG_FILE if os.path.exists(SESSION_LOG_FILE) else LOG_FILE
    return _total_from_file(target_file)

#Ito ang mfunction para i-zero out ang dashboard nang hindi binubura ang permanent history
def reset_session_logs():
    with open(SESSION_LOG_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()

#kinukuha ang pinaka-latest na profile para hindi na mano-manong mag-input ang user."
def load_last_user():
    if not os.path.exists(USERS_FILE):
        return None

    try:
        with open(USERS_FILE, newline="") as f:
            reader = csv.DictReader(f)
            last_row = None
            for row in reader:
                last_row = row
    except (FileNotFoundError, csv.Error):
        return None

    return last_row


def save_user_record(name, weight, age, goal, protein_goal):
    """Para maipakitang naka-log ang bawat profile save sa users.csv bilang audit trail."""
    file_exists = os.path.exists(USERS_FILE)

    with open(USERS_FILE, "a", newline="") as f:
        fieldnames = ["Name", "Weight", "Age", "Goal", "ProteinGoal"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "Name": name,
            "Weight": weight,
            "Age": age,
            "Goal": goal,
            "ProteinGoal": protein_goal
        })


def save_session_profile(profile_data):
    """Tinitiyak na kahit i-exit ang app, alam ng system ang huling target at user info."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile_data, f)


def load_session_profile():
    """Binabasa ang huling sine-save na profile para manatiling pareho ang target sa restart."""
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

#Helper na para may header ang CSV at maayos ang format bago isulat ang bagong row
def _append_log(file_path, row):
    needs_header = True
    try:
        with open(file_path, "r", newline='') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames == FIELDNAMES:
                needs_header = False
    except (FileNotFoundError, csv.Error):
        needs_header = True

    with open(file_path, "a", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if needs_header:
            writer.writeheader()
        writer.writerow(row)

#Helper na kumukuha ng kabuuang protein para sa kasalukuyang petsa mula sa anumang CSV.
def _total_from_file(file_path):
    total = 0
    try:
        with open(file_path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Date') == str(date.today()):
                    total += float(row['Protein'])
    except FileNotFoundError:
        return 0
    return round(total, 2)
