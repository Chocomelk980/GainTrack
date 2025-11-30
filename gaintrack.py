import customtkinter as ctk
import tkinter as tk  # Still needed para sa some widgets like Toplevel at Text widgets
from datetime import date  # Para sa date tracking ng protein intake logs
from datafunctions import (
    load_foods,
    add_log,
    total_today,
    reset_session_logs,
    save_user_record,
    save_session_profile,
    load_session_profile,
    LOG_FILE,
    STATE_FILE
)
from userfunctions import (
    calculate_protein,
    validate_age_input,
    validate_weight_input,
    validate_name_input,
    calculate_protein_goal,
    validate_amount_input
)
import os
from tkinter import messagebox
from PIL import Image,ImageTk


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")  

root = ctk.CTk()  # Main window ng application
root.title("GainTrack - Protein Intake Monitoring System with GUI")
root.state("zoomed")  # Fullscreen mode para maximize ang screen space at better user experience

# Get screen dimensions and scaling factor 
# Kinukuha namin ang screen dimensions para ma-adapt ang UI sa different screen sizes
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

scale = min(screen_width / 1920, screen_height / 1080)  # base scaling on 1080p reference

# Colors & Fonts 
BG_COLOR = "#1E1E2F"  
FRAME_BG = "#2E2E3E"  
ENTRY_BG = "#3A3A4A"  
ACCENT_COLOR = "#FF4C29"  # Orange-red for progress
SUCCESS_COLOR = "#4CAF50"  # Green color when goal is reached - Material Design green, fits dark theme
TEXT_COLOR = "#FFFFFF"  

# Fonts na scalable based sa screen size. int() para whole number ang font size
FONT_TITLE = ("Arial", int(28*scale), "bold")  
FONT_LABEL = ("Arial", int(20*scale))  
FONT_BUTTON = ("Arial", int(14*scale), "bold")  

FOOD_SUGGESTIONS = {
    "BULKING": {
        "emoji": "🥩",
        "title": "Here are the food that you can consider!",
        "items": [
            "Peanut Butter",
            "Cheese",
            "Almonds",
            "Rice",
            "Chicken",
            "Egg",
            "Salmon",
            "Pork",
            "Beef",
            "Whole Milk",
            "Soy Milk"
        ]
    },
    "MAINTENANCE": {
        "emoji": "🥗",
        "title": "Here are the food that you can consider!",
        "items": [
            "Chicken",
            "Tofu",
            "Greek Yogurt",
            "Cottage Cheese",
            "Oats",
            "Egg",
            "Shrimp"
        ]
    },
    "CUTTING": {
        "emoji": "🥦",
        "title": "Here are the food that you can consider!",
        "items": [
            "Chicken Breast",
            "Tuna",
            "Shrimp",
            "Egg (remove the yolk)",
            "Milk",
            "Tofu"
        ]
    }
}

# Load food database from CSV file - dictionary format: {food_name: protein_per_100g}
food_data = load_foods()
protein_goal = 0  # Default state habang wala pang saved profile - will be updated pag may profile na
suggestion_icon_var = tk.StringVar(value="🍽️")
suggestion_title_var = tk.StringVar(value="Pick a goal to view a sample plate")
suggestion_details_var = tk.StringVar(value="Tap Bulking, Cutting, or Maintenance to see ideas.")

# Functions
def save_profile():
    global protein_goal  # Need to modify global variable para ma-update ang protein goal
    # Input validation - strip() para tanggalin ang whitespace sa start/end
    name = name_entry.get().strip()
    if not name:  # Check kung may input ba, empty string is falsy
        messagebox.showerror("Error", "Please enter your name.")
        return  # Early return para hindi na ituloy kung invalid
    try:
        weight = float(weight_entry.get())  # Convert to float, will raise ValueError if invalid
    except ValueError:  # Catch error kung hindi valid number ang input
        messagebox.showerror("Error", "Enter a valid weight.")
        return
    age_value = age_entry.get().strip()
    if not age_value:
        messagebox.showerror("Error", "Please enter your age.")
        return  
    goal = goal_var.get()  # Get selected goal from combobox
    if not goal:  # Check kung may na-select na goal
        messagebox.showerror("Error", "Select a goal.")
        return
    # Calculate protein goal based sa weight at fitness goal (bulking/cutting/maintenance)
    protein_goal = calculate_protein_goal(weight, goal)
    update_progress()  # Update UI para makita agad ang new goal
    # Truncate long names para hindi ma-overflow at ma-break ang rounded corners ng frame
    display_name = name if len(name) <= 25 else name[:22] + "..."
    profile_title_label.configure(text=f"Hello, {display_name}! Welcome to GainTrack!")  # Personalize greeting

    # If lahat ng fields may input, these line of codes will disable editing
    name_entry.configure(state="disabled")
    weight_entry.configure(state="disabled")
    age_entry.configure(state="disabled")
    goal_menu.configure(state="disabled")

    # Dictionary para sa easy data handling - structured format
    profile_data = {
        "Name": name,
        "Weight": weight,
        "Age": age_value,
        "Goal": goal,
        "ProteinGoal": protein_goal
    }

    # Save sa users.csv para sa audit trail - permanent record ng lahat ng profiles
    save_user_record(name, weight, age_value, goal, protein_goal)
    # Save sa current_profile.json para sa session persistence - ma-reload pag restart ng app
    save_session_profile(profile_data)
    messagebox.showinfo("Profile Saved", f"Daily Protein Goal: {protein_goal}g")  # User feedback

def load_saved_profile():
    global protein_goal  # Modify global variable
    # Load saved profile from JSON file (current_profile.json) - session persistence
    profile_source = load_session_profile()
    if not profile_source:  # If walang saved profile, exit function
        return
    try:
        # Get protein goal from saved data, default to 0 if wala
        # get() method para safe - hindi mag-error kung wala ang key
        protein_goal = float(profile_source.get("ProteinGoal", 0))
    except (TypeError, ValueError):  # Catch errors kung hindi valid number
        protein_goal = 0  # Fallback to 0 kung may error

    # Extract saved values from profile data
    name = profile_source.get("Name", "")
    weight = profile_source.get("Weight", "")
    age = profile_source.get("Age", "")
    goal = profile_source.get("Goal", "")

    # Populate entry fields with saved data - delete existing text first, then insert
    name_entry.delete(0, tk.END)  # Clear from start (0) to end (END)
    name_entry.insert(0, name)  # Insert saved name at position 0
    weight_entry.delete(0, tk.END)
    weight_entry.insert(0, weight)
    age_entry.delete(0, tk.END)
    age_entry.insert(0, age)

    # Check kung valid ang goal value bago i-set (must be in combobox values)
    if goal in goal_menu._values:  # _values is internal attribute ng CTkComboBox
        goal_var.set(goal)

    if name:
        # Truncate long names para hindi ma-overflow at ma-break ang rounded corners ng frame
        display_name = name if len(name) <= 25 else name[:22] + "..."
        profile_title_label.configure(text=f"Hello, {display_name}! Welcome to GainTrack!")

def update_progress():
    # Get total protein intake for today from session logs or main logs
    today_total = total_today()
    # Calculate progress fraction (0.0 to 1.0). min() para hindi lumampas sa 1.0 (100%)
    # Ternary operator: if protein_goal > 0, calculate fraction, else 0
    fraction = min(today_total / protein_goal, 1.0) if protein_goal > 0 else 0
    progress.set(fraction)  # Update progress bar (0.0 to 1.0 range)

    # Update display text - show current/target format, handle zero goal case
    protein_display.configure(
        text=f"{today_total}g / {protein_goal}g" if protein_goal > 0 else f"{today_total}g / 0g"
    )
    # Disable add button kung na-reach na ang goal (prevent over-logging)
    # Enable lang kung walang goal pa or hindi pa na-reach
    add_btn.configure(state="disabled" if protein_goal > 0 and today_total >= protein_goal else "normal")
    # Change progress bar color: green if goal reached, orange-red if progress, default if no progress
    if protein_goal > 0 and today_total >= protein_goal:
        progress.configure(progress_color=SUCCESS_COLOR)  # Green when goal reached
    elif today_total > 0:
        progress.configure(progress_color=ACCENT_COLOR)  # Orange-red when there's progress
    else:
        progress.configure(progress_color=progress._fg_color)  # Default color when no progress

def log_food():
    # Get selected food from combobox
    food = food_var.get()
    if not food:  # Validation: check kung may na-select na food
        messagebox.showwarning("Missing", "Please select a food item.")
        return
    try:
        amount = float(amount_entry.get())  # Convert amount to float (grams)
        if amount == 0:
            messagebox.showerror("Error", "Amount cannot be zero.")
            return
    except ValueError:  # Catch error kung hindi valid number
        messagebox.showerror("Error", "Enter a valid number for amount.")
        return

    # Calculate protein content: (protein_per_100g / 100) * amount_in_grams
    protein = calculate_protein(food_data, food, amount)
    # Save log entry to both session_logs.csv and logs.csv (dual logging system)
    add_log(food, amount, protein)
    update_progress()  # Refresh UI to show updated totals
    messagebox.showinfo("Logged", f"{protein}g of protein added from {food}!")  # User feedback
    # Check if goal reached after logging - congratulate user
    if protein_goal > 0 and total_today() >= protein_goal:
        messagebox.showinfo("Goal Reached!", f"You've reached your daily protein goal of {protein_goal}g!")

def clear_program():
    global protein_goal  # Modify global variable

    #return them back to normal, so we can clear them again
    name_entry.configure(state="normal")
    weight_entry.configure(state="normal")
    age_entry.configure(state="normal")
    goal_menu.configure(state="normal")

    # Clear all input fields - reset to empty/default state
    food_var.set("")  
    amount_entry.delete(0, tk.END)  
    name_entry.delete(0, tk.END)  
    weight_entry.delete(0, tk.END)  
    age_entry.delete(0, tk.END)  
    goal_var.set("")  
    profile_title_label.configure(text=PROFILE_HEADING)  
    reset_session_logs()  
    protein_goal = 0  
    update_progress()  
    add_btn.configure(state="normal")  # Re-enable add button
    

    # Delete session profile file para hindi ma-reload ang old profile
    if os.path.exists(STATE_FILE):  # Check kung exists bago i-delete (safe deletion)
        os.remove(STATE_FILE)

    messagebox.showinfo("Reset", "Program has been fully reset!")  # User confirmation


def show_history():
    # Check kung may log file na - if wala, inform user
    if not os.path.exists(LOG_FILE):
        messagebox.showinfo("History", "No history available yet.")
        return
    # Create new window (Toplevel) para sa history view - separate from main window
    history_window = tk.Toplevel(root)  # tk.Toplevel kasi walang CTk equivalent for popup windows
    history_window.title("History")
    # Scale window size based sa screen resolution para responsive
    history_window.geometry(f"{int(500*scale)}x{int(400*scale)}")
    history_window.configure(bg=BG_COLOR)  # Match main window background

    tk.Label(
        history_window,
        text="Protein Intake History",
        font=("Arial", int(16*scale), "bold"),
        bg=BG_COLOR,
        fg=TEXT_COLOR
    ).pack(pady=int(10*scale))

    content_frame = tk.Frame(history_window, bg=BG_COLOR)
    content_frame.pack(fill="both", expand=True, padx=int(10*scale), pady=(0, int(10*scale)))

    # Text widget para sa history display - tk.Text kasi mas suitable for multi-line text
    text_box = tk.Text(content_frame, width=50, height=15, bg=ENTRY_BG, fg=TEXT_COLOR, font=("Arial", int(12*scale)))
    text_box.pack(side="left", fill="both", expand=True)  # Left side, expandable

    # Scrollbar para sa long history - connect sa text widget
    scrollbar = tk.Scrollbar(content_frame, command=text_box.yview)  # Vertical scrolling
    scrollbar.pack(side="right", fill="y")  # Right side, vertical fill
    text_box.config(yscrollcommand=scrollbar.set)  # Two-way binding para synchronized scrolling

    # Read log file line by line and display sa text widget
    with open(LOG_FILE, "r") as file:  # Context manager para automatic file closing
        for line in file:
            text_box.insert(tk.END, line)  # Insert each line at end of text widget
    text_box.config(state="disabled")  # Make read-only para hindi ma-edit ng user

    btn_frame = ctk.CTkFrame(history_window, fg_color="transparent")
    btn_frame.pack(pady=int(5*scale))
    reset_btn = ctk.CTkButton(
        btn_frame,
        text="Reset History",
        command=reset_history,
        fg_color=ACCENT_COLOR,
        hover_color="#FF6A42",
        font=FONT_BUTTON,
        corner_radius=int(15*scale),
        width=int(200*scale),
        height=int(40*scale)
    )
    reset_btn.pack()

def reset_history():
    # Check kung may history file na
    if not os.path.exists(LOG_FILE):
        messagebox.showinfo("Reset History", "No history to reset.")
        return

    # Confirmation dialog para maiwasan ang accidental deletion - important safety feature
    confirm = messagebox.askyesno("Confirm Reset", "Are you sure you want to delete ALL history?")
    if not confirm:  # If user clicked No, exit function
        return

    # Clear the log file - "w" mode overwrites existing file, creates new empty file
    with open(LOG_FILE, "w") as file:
        file.write("")  # Write empty string para ma-clear ang file

    # Clear the Text widget in the history window - traverse widget hierarchy
    # Nested loops para hanapin ang Text widget sa history window
    for widget in root.winfo_children():  # Get all child widgets of root
        if isinstance(widget, tk.Toplevel):  # check for history window (Toplevel)
            for child in widget.winfo_children():  # Get children of history window
                if isinstance(child, tk.Frame):  # content_frame
                    for subchild in child.winfo_children():  # Get children of frame
                        if isinstance(subchild, tk.Text):  # Found the text widget
                            subchild.config(state="normal")  # Enable editing temporarily
                            subchild.delete("1.0", tk.END)  # Delete from line 1, char 0 to end
                            subchild.config(state="disabled")  # Make read-only again
    
    messagebox.showinfo("Reset History", "History has been cleared!")


def show_food_suggestion(goal_key):
    """Update the food suggestion panel based on selected goal."""
    goal = (goal_key or "").upper()
    suggestion = FOOD_SUGGESTIONS.get(goal)

    if not suggestion:
        suggestion_icon_var.set("🍽️")
        suggestion_title_var.set("More ideas coming soon")
        suggestion_details_var.set("We will add additional meal ideas for this goal.")
        return

    suggestion_icon_var.set(suggestion.get("emoji", "🍽️"))
    suggestion_title_var.set(suggestion.get("title", "Recommended Plate"))
    details = "\n".join(f"• {item}" for item in suggestion.get("items", []))
    suggestion_details_var.set(details or "Enjoy a balanced meal tailored to your plan.")


# GUI Layout
PROFILE_HEADING = "Set Your Profile"

top_frame = ctk.CTkFrame(root, corner_radius=0, fg_color=BG_COLOR)
top_frame.pack(fill="x")

title_label = ctk.CTkLabel(top_frame, text="GainTrack", font=FONT_TITLE, fg_color=None, text_color=TEXT_COLOR)
title_label.pack(pady=(30*scale, 5*scale))

date_label = ctk.CTkLabel(top_frame, text=date.today().strftime("%B %d, %Y"), font=("Arial", int(16*scale)), fg_color=None, text_color=TEXT_COLOR)
date_label.pack()

protein_display = ctk.CTkLabel(top_frame, text="0g / 0g", font=("Arial", int(42*scale), "bold"), fg_color=None, text_color=TEXT_COLOR)
protein_display.pack(pady=(10*scale, 20*scale))

# Logo
logo_image = Image.open(r"C:\Users\Ryzen5\GainTrack\GainTrack (5).png")
logo_image = logo_image.resize((120, 120))
logo_photo = ImageTk.PhotoImage(logo_image)

logo_label = ctk.CTkLabel(root, image=logo_photo, text="", fg_color=BG_COLOR)
logo_label.image = logo_photo
logo_label.pack(side="top")
logo_label.place(relx=0.0, rely=0.0, anchor="nw", x=10, y=10)


main_frame = ctk.CTkFrame(root, corner_radius=int(20*scale), fg_color=FRAME_BG)
main_frame.pack(fill="both", expand=True, pady=int(10*scale), padx=int(20*scale))

# Progress bar para visual representation ng protein goal progress
progress = ctk.CTkProgressBar(main_frame, width=int(800*scale), height=int(50*scale), progress_color=ACCENT_COLOR)
progress.pack(pady=int(20*scale))  # Vertical padding para spacing

# Content layout: left (main system) + right (recommendations)
content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
content_frame.pack(fill="both", expand=True, padx=int(10*scale), pady=int(10*scale))
content_frame.grid_columnconfigure(0, weight=3)
content_frame.grid_columnconfigure(1, weight=2)
content_frame.grid_rowconfigure(0, weight=1)

left_column = ctk.CTkFrame(content_frame, fg_color="transparent")
left_column.grid(row=0, column=0, sticky="nsew", padx=int(10*scale), pady=int(10*scale))
left_column.grid_rowconfigure(0, weight=0)
left_column.grid_rowconfigure(1, weight=0)
left_column.grid_rowconfigure(2, weight=0)
left_column.grid_rowconfigure(3, weight=1)

# Wrapper para consistent horizontal alignment ng main system widgets
system_wrapper = ctk.CTkFrame(left_column, fg_color="transparent", width=int(720*scale))
system_wrapper.pack(fill="both", expand=True, padx=int(10*scale), anchor="center")
system_wrapper.pack_propagate(False)


right_column = ctk.CTkFrame(content_frame, fg_color="transparent")
right_column.grid(row=0, column=1, sticky="nsew", padx=int(10*scale), pady=int(10*scale))
right_column.grid_rowconfigure(0, weight=1)

# Profile frame - pack_propagate(False) para hindi mag-expand ang frame based sa content, maintaining rounded corners
profile_frame = ctk.CTkFrame(system_wrapper, corner_radius=int(50*scale), fg_color=ENTRY_BG, width=int(550*scale), height=int(350*scale))
profile_frame.pack(pady=int(20*scale), padx=int(15*scale), anchor="center")
profile_frame.pack_propagate(False)  # Prevent frame from expanding, maintains rounded corners
# Use grid directly on profile_frame para maiwasan ang overlapping frame issue
profile_frame.grid_columnconfigure(0, weight=1)
profile_frame.grid_rowconfigure(0, weight=1)
# Match the frame color instead of transparent para hindi makita ang separate frame
profile_content = ctk.CTkFrame(profile_frame, fg_color=ENTRY_BG, corner_radius=0, border_width=0)
# Use grid with padding instead of place() para better control at maiwasan ang overlap
profile_content.grid(row=0, column=0, padx=int(20*scale), pady=int(20*scale), sticky="nsew")

# Title label - width limit para hindi ma-overflow at ma-break ang rounded corners
profile_title_label = ctk.CTkLabel(profile_content, text=PROFILE_HEADING, font=("Segoe UI", int(25*scale), "bold"), 
                                    fg_color=None, text_color=TEXT_COLOR, width=int(500*scale))
profile_title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20*scale))

# Entries
ctk.CTkLabel(
    profile_content, 
    text="Name:", 
    font=FONT_LABEL, 
    fg_color=None, 
    text_color=TEXT_COLOR

    ).grid(row=1, column=0, padx=int(10*scale), pady=int(10*scale), sticky="e")
name_entry = ctk.CTkEntry(profile_content, width=int(280*scale), height=int(35*scale), corner_radius=int(10*scale),
                          validate="key", validatecommand=(root.register(validate_name_input), "%P"))
name_entry.grid(row=1, column=1, padx=int(10*scale), pady=int(10*scale))

ctk.CTkLabel(
    profile_content, 
    text="Weight (kg):", 
    font=FONT_LABEL, 
    fg_color=None, 
    text_color=TEXT_COLOR
    ).grid(row=2, column=0, padx=int(10*scale), pady=int(10*scale), sticky="e")
weight_entry = ctk.CTkEntry(profile_content, width=int(280*scale), height=int(35*scale), corner_radius=int(10*scale),
                             validate="key", validatecommand=(root.register(validate_weight_input), "%P"))
weight_entry.grid(row=2, column=1, padx=int(10*scale), pady=int(10*scale))  # Grid layout for alignment

ctk.CTkLabel(   
    profile_content, 
    text="Age:", 
    font=FONT_LABEL, 
    fg_color=None, 
    text_color=TEXT_COLOR
    ).grid(row=3, column=0, padx=int(10*scale), pady=int(10*scale), sticky="e")

# Prevents invalid characters from being entered (e.g., letters in age field)
age_entry = ctk.CTkEntry(profile_content, width=int(280*scale), height=int(35*scale), corner_radius=int(10*scale),
                          validate="key", validatecommand=(root.register(validate_age_input), "%P"))
age_entry.grid(row=3, column=1, padx=int(10*scale), pady=int(10*scale))

ctk.CTkLabel(
    profile_content, 
    text="Goal:", 
    font=FONT_LABEL, 
    fg_color=None, 
    text_color=TEXT_COLOR
    ).grid(row=4, column=0, padx=int(10*scale), pady=int(10*scale), sticky="e")
    
# StringVar para sa two-way data binding - automatic update ng variable when selection changes
goal_var = tk.StringVar()
# ComboBox para sa dropdown selection - readonly para hindi ma-type ng user, dapat pili lang
# Three fitness goals: BULKING (gain muscle), CUTTING (lose fat), MAINTENANCE (maintain weight)
goal_menu = ctk.CTkComboBox(profile_content, width=int(280*scale), height=int(35*scale),
                             values=["BULKING", "CUTTING", "MAINTENANCE"], variable=goal_var, corner_radius=int(10*scale),
                             state="readonly")  # readonly prevents manual typing, ensures valid selection
goal_menu.grid(row=4, column=1, padx=int(10*scale), pady=int(10*scale))

ctk.CTkButton(profile_content, text="Save Profile", font=FONT_LABEL, command=save_profile,
              fg_color=ACCENT_COLOR, hover_color="#FF6A42", corner_radius=int(15*scale),
              width=int(200*scale), height=int(30*scale)).grid(row=5, column=0, columnspan=2, pady=int(20*scale))

# ----------------- Food & Buttons Frames -----------------
# Food Input
input_frame = ctk.CTkFrame(system_wrapper, corner_radius=int(20*scale), fg_color=ENTRY_BG, width=int(450*scale), height=int(150*scale))
input_frame.pack(pady=int(10*scale), padx=int(15*scale), anchor="center")
# pack_propagate(False) para hindi mag-shrink ang frame based sa content
# Ensures consistent frame size regardless of content - better layout control
input_frame.pack_propagate(False)

input_content = ctk.CTkFrame(input_frame, fg_color="transparent")
input_content.place(relx=0.5, rely=0.5, anchor="center")
# grid_columnconfigure para sa responsive column sizing
# weight=1 means column 1 (input fields) will expand to fill available space
input_content.grid_columnconfigure(1, weight=1)

ctk.CTkLabel(input_content, text="Select Food:", font=FONT_LABEL, fg_color=None, text_color=TEXT_COLOR).grid(row=0, column=0, padx=int(10*scale), pady=int(10*scale), sticky="e")
food_var = tk.StringVar()
# Populate combobox with food names from database - list(food_data.keys()) converts dict keys to list
# Readonly para hindi ma-type ng user, dapat select lang from predefined foods
food_menu = ctk.CTkComboBox(input_content, values=list(food_data.keys()), variable=food_var,
                             corner_radius=int(10*scale), state="readonly", width=int(200*scale), height=int(35*scale))
food_menu.grid(row=0, column=1, padx=int(10*scale), pady=int(10*scale), sticky="ew")

ctk.CTkLabel(input_content, text="Amount (grams):", font=FONT_LABEL, fg_color=None, text_color=TEXT_COLOR).grid(row=1, column=0, padx=int(10*scale), pady=int(10*scale), sticky="e")
amount_entry = ctk.CTkEntry(input_content, width=int(200*scale), height=int(35*scale), validate="key", validatecommand=(root.register(validate_amount_input), "%P"), corner_radius=int(10*scale))
amount_entry.grid(row=1, column=1, padx=int(10*scale), pady=int(10*scale), sticky="ew")

# Buttons
add_btn_frame = ctk.CTkFrame(system_wrapper, corner_radius=int(20*scale), fg_color=FRAME_BG, width=int(700*scale), height=int(100*scale))
add_btn_frame.pack(pady=int(20*scale), padx=int(15*scale), anchor="center")
add_btn_frame.pack_propagate(False)

buttons_content = ctk.CTkFrame(add_btn_frame, fg_color="transparent", width=int(600*scale), height=int(50*scale))
buttons_content.place(relx=0.5, rely=0.5, anchor="center")
buttons_content.pack_propagate(False)
# Configure all three columns (0, 1, 2) with equal weight para equal spacing ng buttons
# weight=1 means each column gets equal share of available space
buttons_content.grid_columnconfigure((0,1,2), weight=1)

history_btn = ctk.CTkButton(buttons_content, text="History", command=show_history,
                            fg_color=ACCENT_COLOR, hover_color="#FF6A42", corner_radius=int(15*scale),
                            width=int(200*scale), height=int(30*scale), font=FONT_LABEL)
history_btn.grid(row=0, column=0, padx=int(10*scale), sticky="ew")

add_btn = ctk.CTkButton(buttons_content, text="+ Add Protein", command=log_food,
                        fg_color=ACCENT_COLOR, hover_color="#FF6A42", corner_radius=int(15*scale),
                        width=int(200*scale), height=int(30*scale), font=FONT_LABEL)
add_btn.grid(row=0, column=1, padx=int(10*scale), sticky="ew")

clear_btn = ctk.CTkButton(buttons_content, text="Clear", command=clear_program,
                          fg_color=ACCENT_COLOR, hover_color="#FF6A42", corner_radius=int(15*scale),
                          width=int(200*scale), height=int(30*scale), font=FONT_LABEL)
clear_btn.grid(row=0, column=2, padx=int(10*scale), sticky="ew")

# ----------------- Food Suggestions Panel (Right Column) -----------------
suggestions_frame = ctk.CTkFrame(right_column, corner_radius=int(30*scale), fg_color=ENTRY_BG)
suggestions_frame.pack(fill="both", expand=True)

ctk.CTkLabel(
    suggestions_frame,
    text="Food Suggestions",
    font=("Segoe UI", int(26*scale), "bold"),
    text_color=TEXT_COLOR
).pack(pady=(int(20*scale), int(10*scale)))

ctk.CTkLabel(
    suggestions_frame,
    text="Choose your goal and try our suggested meals/foods.",
    font=("Arial", int(16*scale)),
    text_color=TEXT_COLOR,
    wraplength=int(320*scale)
).pack(padx=int(20*scale))

goal_buttons = ctk.CTkFrame(suggestions_frame, fg_color="transparent")
goal_buttons.pack(pady=int(20*scale), padx=int(20*scale), fill="x")
goal_buttons.grid_columnconfigure((0, 1, 2), weight=1, uniform="goals")

ctk.CTkButton(
    goal_buttons,
    text="Bulking",
    command=lambda: show_food_suggestion("BULKING"),
    fg_color=ACCENT_COLOR,
    hover_color="#FF6A42",
    corner_radius=int(15*scale),
    font=FONT_BUTTON
).grid(row=0, column=0, padx=int(5*scale), sticky="ew")

ctk.CTkButton(
    goal_buttons,
    text="Maintenance",
    command=lambda: show_food_suggestion("MAINTENANCE"),
    fg_color=ACCENT_COLOR,
    hover_color="#FF6A42",
    corner_radius=int(15*scale),
    font=FONT_BUTTON
).grid(row=0, column=1, padx=int(5*scale), sticky="ew")

ctk.CTkButton(
    goal_buttons,
    text="Cutting",
    command=lambda: show_food_suggestion("CUTTING"),
    fg_color=ACCENT_COLOR,
    hover_color="#FF6A42",
    corner_radius=int(15*scale),
    font=FONT_BUTTON
).grid(row=0, column=2, padx=int(5*scale), sticky="ew")

suggestion_display = ctk.CTkFrame(suggestions_frame, corner_radius=int(25*scale), fg_color=FRAME_BG)
suggestion_display.pack(fill="both", expand=True, padx=int(20*scale), pady=(0, int(20*scale)))
suggestion_display.pack_propagate(False)

suggestion_icon_label = ctk.CTkLabel(
    suggestion_display,
    textvariable=suggestion_icon_var,
    font=("Segoe UI Emoji", int(64*scale))
)
suggestion_icon_label.pack(pady=(int(20*scale), int(10*scale)))

ctk.CTkLabel(
    suggestion_display,
    textvariable=suggestion_title_var,
    font=("Segoe UI", int(22*scale), "bold"),
    text_color=TEXT_COLOR,
    wraplength=int(320*scale)
).pack(padx=int(20*scale), pady=(0, int(10*scale)))

ctk.CTkLabel(
    suggestion_display,
    textvariable=suggestion_details_var,
    font=("Arial", int(16*scale)),
    text_color=TEXT_COLOR,
    justify="left",
    wraplength=int(320*scale)
).pack(padx=int(20*scale), pady=(0, int(20*scale)), fill="both", expand=True)

# Optional: default suggestion view on startup
show_food_suggestion(None)

# Start
# Load saved profile on startup para ma-restore ang previous session
load_saved_profile()
# Update progress bar and display para ma-show ang current state
update_progress()
# mainloop() blocks execution until window is closed
root.mainloop()
