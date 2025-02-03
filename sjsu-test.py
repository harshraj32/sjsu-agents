import tkinter as tk
from tkinter import ttk, messagebox
import pexpect
import sys
import random
import time
import re
import threading
import webbrowser
import subprocess
from tkinter import ttk

class HPCSessionManager:
    def __init__(self, username, password, use_gpu, cpu_time, num_nodes, num_tasks):
        self.username = username
        self.password = password
        self.use_gpu = use_gpu
        self.cpu_time = cpu_time
        self.num_nodes = num_nodes
        self.num_tasks = num_tasks
        self.port = random.randint(10000, 63999)
        self.node_name = None
        self.jupyter_url = None
        self.session = None
        self.tunnel = None

    def request_interactive_session(self, num_nodes, num_tasks, cpu_time):
        """Logs into the HPC, requests an interactive node, and starts Jupyter Notebook."""
        command = f"srun --ntasks={num_tasks} --nodes={num_nodes} --cpus-per-task=4 --time={cpu_time} --pty /bin/bash"

        try:
            print("🔗 Connecting to HPC and requesting a node...")
            self.session = pexpect.spawn(f"ssh {self.username}@coe-hpc1.sjsu.edu", timeout=30)
            self.session.logfile = sys.stdout.buffer  # Log output for debugging

            # Login
            self.session.expect(r"Password:")
            self.session.sendline(self.password)
            self.session.expect(r"\[.*@.* ~\]\$", timeout=30)  # Expect shell prompt
            print("✔ Successfully connected to the HPC login node.")

            # Request an interactive session
            self.session.sendline(command)
            time.sleep(5)  # Allow some time for allocation
            # Check if session is allocated
            print("🔄 Checking allocated node...")
            self.session.sendline("echo $SHELL")
            self.session.expect(r"\[.*@.* ~\]\$", timeout=20)  # Expect shell prompt after running the command

            # Get the shell output and the prompt
            shell_output = self.session.before.decode()
            raw_prompt = self.session.after.decode()

            print(f"Shell output: {shell_output}")
            print(f"Detected prompt: {raw_prompt}")

            # Check if session is allocated
            print("🔄 Checking allocated node...")
            self.session.sendline("hostname")
            self.session.expect(r"(\w+)", timeout=20)

            match = re.search(r"@(\w+)", raw_prompt)
            if match:
                self.node_name = match.group(1)
                if self.node_name != "coe-hpc1":  # Not the login node
                    print(f"Interactive session allocated. Node: {self.node_name}")
                else:
                    print("Still on the login node.")
            else:
                print("No valid node prompt detected.")

            if self.node_name == "coe-hpc1":
                print("❌ Error: Allocation failed. Still on the login node.")
                return False

            time.sleep(5)

            # Load Python and start Jupyter Notebook in background
            print("🚀 Starting Jupyter Notebook...")
            self.session.sendline(f"module load python3; jupyter notebook --no-browser --port={self.port}")
            self.session.expect(r"token=([\w\d]+)", timeout=20)  # Expect PID of Jupyter process

            token = self.session.match.group(1).decode()
            self.jupyter_url = f"http://127.0.0.1:{self.port}/?token={token}"

            print(f"✔ Jupyter Notebook running at: {self.jupyter_url}")
            

            if not self.setup_ssh_tunnel():
                return False, None

            return True, self.jupyter_url

        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        


    def setup_ssh_tunnel(self):
        """Sets up a persistent SSH tunnel."""
        try:
            print("🔗 Setting up SSH tunnel to login node...")
            self.tunnel = pexpect.spawn(f"ssh -L {self.port}:localhost:{self.port} {self.username}@coe-hpc1.sjsu.edu", timeout=30)

            self.tunnel.expect(r"Password:")
            self.tunnel.sendline(self.password)
            self.tunnel.expect(r"\[.*@.* ~\]\$", timeout=30)
            print("✔ Connected to login node.")

            print(f"🔗 Forwarding port to compute node: {self.node_name}...")
            self.tunnel.sendline(f"ssh -L {self.port}:localhost:{self.port} {self.username}@{self.node_name}")
            self.tunnel.expect(r"\[.*@.* ~\]\$", timeout=30)
            print(f"✔ SSH tunnel established to {self.node_name}")

            return True
        except Exception as e:
            print(f"❌ SSH Tunnel Error: {e}")
            return False

    def start(self, num_nodes, num_tasks, cpu_time):
        def session_wrapper():
            self.request_interactive_session(num_nodes, num_tasks, cpu_time)
            if not self.node_name:
                root.after(0, lambda: messagebox.showerror("Error", "Failed to start Jupyter Notebook."))
            else:
                root.after(0, lambda: update_jupyter_button(self.jupyter_url))

        session_thread = threading.Thread(target=session_wrapper)
        session_thread.start()
        session_thread.join()

        if not self.node_name:
            return False

        tunnel_thread = threading.Thread(target=self.setup_ssh_tunnel)
        tunnel_thread.start()
        tunnel_thread.join()
        return True

def run_hpc_job():
    username = username_entry.get()
    password = password_entry.get()
    use_gpu = gpu_var.get()
    num_nodes = int(nodes_entry.get())
    cpu_time = time_entry.get()
    num_tasks = int(tasks_entry.get())

    session_manager = HPCSessionManager(username, password, use_gpu, cpu_time, num_nodes, num_tasks)
    status_label.config(text="Requesting compute resources...")
    root.update()

    if not session_manager.start(num_nodes, num_tasks, cpu_time):
        status_label.config(text="❌ HPC Job Failed.")
        return

    status_label.config(text="Jupyter Notebook created successfully!")
    jupyter_button.config(state=tk.NORMAL, text="Open Jupyter", command=lambda: open_jupyter(session_manager.jupyter_url))

def launch_job():
    threading.Thread(target=run_hpc_job).start()

def open_jupyter(url):
    if url:
        webbrowser.open(url)
    else:
        messagebox.showerror("Error", "Jupyter URL not available.")


def show_running_jobs():
    """Logs into HPC, fetches running jobs, and displays them in a table."""
    try:
        username = username_entry.get()
        password = password_entry.get()

        # Establish SSH session
        session = pexpect.spawn(f"ssh {username}@coe-hpc1.sjsu.edu", timeout=30)
        session.logfile = sys.stdout.buffer  # Debugging output

        # Login
        session.expect(r"Password:")
        session.sendline(password)
        session.expect(r"\[.*@.* ~\]\$", timeout=30)  # Expect shell prompt
        print("✔ Successfully connected to the HPC login node.")

        # Run squeue command
        session.sendline(f"squeue -u {username}")
        session.expect(r"\[.*@.* ~\]\$", timeout=30)  # Wait for command to complete
        output = session.before.decode().split("\n")[1:]  # Skip header

        # Clear existing table data
        for row in jobs_table.get_children():
            jobs_table.delete(row)

        # Parse output and insert into table
        for i, line in enumerate(output[1:]):
            if line.strip():
                parts = line.split()
                if len(parts) >= 7:  # Ensure correct format
                    tag = 'even' if i % 2 == 0 else 'odd'
                    jobs_table.insert("", tk.END, values=(
                        parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6]
                    ), tags=(tag,))

        session.close()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch running jobs: {e}")

def delete_job(item):
    """Deletes a selected job and refreshes the table."""
    try:
        username = username_entry.get()
        password = password_entry.get()
        job_id = jobs_table.item(item, "values")[0]
        
        session = pexpect.spawn(f"ssh {username}@coe-hpc1.sjsu.edu", timeout=30)
        session.expect(r"Password:")
        session.sendline(password)
        session.expect(r"\[.*@.* ~\]\$", timeout=30)
        session.sendline(f"scancel {job_id}")
        session.expect(r"\[.*@.* ~\]\$", timeout=30)
        session.close()

        jobs_table.delete(item)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete job: {e}")

def update_jupyter_button(url):
    jupyter_button.config(state=tk.NORMAL, text="Open Jupyter", command=lambda: open_jupyter(url))


# Initialize main window
root = tk.Tk()
root.title("HPC Jupyter Launcher")
root.geometry("800x600")  # Increased window size

# Styling
style = ttk.Style()
style.configure("TLabel", font=("Arial", 14))
style.configure("TEntry", font=("Arial", 14))
style.configure("TButton", font=("Arial", 14, "bold"), padding=10)
style.configure("Treeview.Heading", font=("Arial", 14, "bold"))
style.configure("Treeview", font=("Arial", 12), rowheight=25)
style.map("TButton", foreground=[('pressed', 'black'), ('active', 'blue')],
          background=[('pressed', '!disabled', 'light blue'), ('active', 'white')])

tabs = ttk.Notebook(root)
tab1 = ttk.Frame(tabs)
tab2 = ttk.Frame(tabs)
tabs.add(tab1, text="Launch Job")
tabs.add(tab2, text="Running Jobs")
tabs.pack(expand=True, fill="both")

frame = ttk.Frame(tab1, padding=20)
frame.pack(pady=10)

ttk.Label(frame, text="Username:").grid(row=0, column=0, sticky="w", pady=5)
username_entry = ttk.Entry(frame)
username_entry.grid(row=0, column=1, pady=5)

ttk.Label(frame, text="Password:").grid(row=1, column=0, sticky="w", pady=5)
password_entry = ttk.Entry(frame, show="*")
password_entry.grid(row=1, column=1, pady=5)

gpu_var = tk.BooleanVar()
gpu_checkbox = ttk.Checkbutton(frame, text="Use GPU", variable=gpu_var)
gpu_checkbox.grid(row=2, columnspan=2, pady=5)

ttk.Label(frame, text="Number of Nodes:").grid(row=3, column=0, sticky="w", pady=5)
nodes_entry = ttk.Entry(frame)
nodes_entry.grid(row=3, column=1, pady=5)

ttk.Label(frame, text="Time (hh:mm:ss):").grid(row=4, column=0, sticky="w", pady=5)
time_entry = ttk.Entry(frame)
time_entry.insert(0, "01:00:00")  # Default value
time_entry.grid(row=4, column=1, pady=5)

ttk.Label(frame, text="Number of Tasks:").grid(row=5, column=0, sticky="w", pady=5)
tasks_entry = ttk.Entry(frame)
tasks_entry.grid(row=5, column=1, pady=5)

launch_button = ttk.Button(frame, text="\U0001F680 Launch Jupyter", command=launch_job)
launch_button.grid(row=6, columnspan=6, pady=10, ipadx=10)

status_label = ttk.Label(frame, text="", font=("Arial", 12, "italic"))
status_label.grid(row=7, columnspan=2, pady=5)

jupyter_button = ttk.Label(frame, text="", state=tk.DISABLED)
jupyter_button.grid(row=8, columnspan=2, pady=5)

tab2_frame = ttk.Frame(tab2, padding=20)
tab2_frame.pack(expand=True, fill="both")

columns = ("Job ID", "Partition", "Name", "User", "State", "Time", "Nodes")
jobs_table = ttk.Treeview(tab2_frame, columns=columns, show="headings", height=15)
for col in columns:
    jobs_table.heading(col, text=col)
    jobs_table.column(col, anchor="center", width=100)

jobs_table.pack(expand=True, fill="both", pady=10)
jobs_table.bind("<Double-1>", lambda e: delete_job(jobs_table.selection()[0]))

refresh_button = ttk.Button(tab2_frame, text="\U0001F504 Refresh Jobs", command=show_running_jobs)
refresh_button.pack(pady=5, ipadx=10)

root.mainloop()