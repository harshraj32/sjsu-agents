import tkinter as tk
from tkinter import ttk, messagebox

# Global list to store running files
running_files = []

# Function to handle Run button click
def run_selected_options():
    selected_option = option_var.get()
    text_input = entry_text.get()
    checkbox_state = check_var.get()
    
    if not selected_option or not text_input:
        messagebox.showwarning("Warning", "Please select an option and enter text!")
        return
    
    # Simulate adding the running file
    file_name = f"{selected_option}_{text_input}.txt"
    running_files.append(file_name)
    
    update_running_files_list()
    messagebox.showinfo("Success", f"File '{file_name}' is now running!")

# Function to update running files list
def update_running_files_list():
    listbox_files.delete(0, tk.END)
    for file in running_files:
        listbox_files.insert(tk.END, file)

# Create the main application window
root = tk.Tk()
root.title("Beautiful UI Application")
root.geometry("600x400")
root.configure(bg="#f0f0f5")

# Create Notebook (Tabbed Interface)
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

# --- CREATE SECTION ---
frame_create = ttk.Frame(notebook)
notebook.add(frame_create, text="Create")

# Dropdown for selecting an option
ttk.Label(frame_create, text="Select Option:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
option_var = tk.StringVar()
dropdown = ttk.Combobox(frame_create, textvariable=option_var, values=["Option 1", "Option 2", "Option 3"], state="readonly")
dropdown.grid(row=0, column=1, padx=10, pady=5)

# Text Input
ttk.Label(frame_create, text="Enter Text:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
entry_text = ttk.Entry(frame_create)
entry_text.grid(row=1, column=1, padx=10, pady=5)

# Checkbox
check_var = tk.IntVar()
checkbox = ttk.Checkbutton(frame_create, text="Enable Feature", variable=check_var)
checkbox.grid(row=2, column=0, columnspan=2, pady=5)

# Run Button
btn_run = ttk.Button(frame_create, text="Run", command=run_selected_options)
btn_run.grid(row=3, column=0, columnspan=2, pady=10)

# --- RUNNING FILES SECTION ---
frame_running = ttk.Frame(notebook)
notebook.add(frame_running, text="Running Files")

# Running Files Listbox
ttk.Label(frame_running, text="Currently Running Files:").pack(pady=5)
listbox_files = tk.Listbox(frame_running, height=10)
listbox_files.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# Start the application loop
root.mainloop()