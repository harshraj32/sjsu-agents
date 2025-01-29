import os
import random
import re
import subprocess
import sys
import time
from getpass import getpass

import pexpect


import time
import pexpect
import sys
import re

import time
import pexpect
import sys
import re

def request_interactive_session(username, password, use_gpu=False, retries=3):
    command = "srun "
    if use_gpu:
        command += "-p gpu --gres=gpu "
    command += "--ntasks=1 --nodes=1 --cpus-per-task=4 --time=04:00:00 --pty /bin/bash"

    for attempt in range(retries):
        try:
            print(f"Attempting to connect to the HPC cluster (attempt {attempt + 1}/{retries})...")
            child = pexpect.spawn(f"ssh {username}@coe-hpc1.sjsu.edu", timeout=30)

            # Log output for debugging
            child.logfile = sys.stdout.buffer

            # Expect the password prompt and send the password
            child.expect(r"Password:")
            child.sendline(password)

            # Wait for the initial shell prompt
            child.expect(r"\[.*@.* ~\]\$", timeout=30)  # Generalized shell prompt
            print("Successfully connected to the cluster. Shell prompt detected.")

            # Send the srun command to request an interactive session
            print("Connection established. Sending interactive session request...")
            child.sendline(command)

            # Introduce a small delay before looking for the prompt or node message
            time.sleep(5)  # You can adjust the delay if needed

            # Run a simple command to check the current shell
            print("Running shell check to determine environment...")
            child.sendline("echo $SHELL")
            child.expect(r"\[.*@.* ~\]\$", timeout=20)  # Expect shell prompt after running the command

            # Get the shell output and the prompt
            shell_output = child.before.decode()
            raw_prompt = child.after.decode()

            print(f"Shell output: {shell_output}")
            print(f"Detected prompt: {raw_prompt}")

            # Check if the prompt is for a node
            match = re.search(r"@(\w+)", raw_prompt)
            if match:
                node_name = match.group(1)
                if node_name != "coe-hpc1":  # Not the login node
                    print(f"Interactive session allocated. Node: {node_name}")
                    return node_name, child
                else:
                    print("Still on the login node.")
            else:
                print("No valid node prompt detected.")
            
        except pexpect.exceptions.TIMEOUT as e:
            print(f"Attempt {attempt + 1} failed due to timeout: {e}")
            if attempt < retries - 1:
                time.sleep(5)  # Wait before retrying
            else:
                print("All attempts failed. Exiting...")
                sys.exit(1)
        except Exception as e:
            print(f"Error while starting the session: {e}")
            sys.exit(1)
            
def setup_jupyter(node_name, username, password, port):
    try:
        print(f"Connecting to node {node_name}...")
        password_prompt = f"Password:|{username}@coe-hpc1.sjsu.edu's Password:"
        child = pexpect.spawn(f"ssh {username}@{node_name}", timeout=60)
        child.expect(password_prompt)
        child.sendline(password)
        child.expect(r"\$", timeout=60)  # Wait for shell prompt
        print("Setting up Jupyter Notebook...")
        child.sendline(
            f"module load python3; jupyter notebook --no-browser --port={port}"
        )
        child.expect(
            r"http://localhost:\d+/\?token=\w+", timeout=120
        )  # Adjusted timeout for Jupyter
        jupyter_url = child.match.group(0).decode()
        print(f"Jupyter URL: {jupyter_url}")
        return jupyter_url.replace("localhost", "127.0.0.1")
    except Exception as e:
        print(f"Error starting Jupyter Notebook: {e}")
        sys.exit(1)


def setup_ssh_tunnel(username, node_name, port):
    try:
        print(f"Setting up SSH tunnel for {node_name}...")
        tunnel = subprocess.Popen(
            [
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                "-L",
                f"{port}:localhost:{port}",
                "-J",
                f"{username}@coe-hpc1.sjsu.edu",
                f"{username}@{node_name}",
                "-N",
            ]
        )
        print(f"SSH tunnel established on port {port}.")
        return tunnel
    except Exception as e:
        print(f"Error setting up SSH tunnel: {e}")
        sys.exit(1)




def main():
    print("SJSU HPC Jupyter Launcher\n")
    username = "017440488"
    if not username:
        print("Error: Username cannot be empty.")
        sys.exit(1)

    password = "Padmini@123456789"
    use_gpu = input("Require GPU? (y/n): ").lower().strip() == "y"
    port = random.randint(10000, 63999)

    print("Requesting compute resources...")
    node_name, session = request_interactive_session(username, password, use_gpu)

    print("Setting up SSH tunnel...")
    tunnel = setup_ssh_tunnel(username, node_name, port)

    print("Launching Jupyter Notebook...")
    jupyter_url = setup_jupyter(node_name, username, password, port)

    print("\nSuccess! Use this URL in your browser:")
    print(jupyter_url)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nClosing connections...")
        tunnel.terminate()
        session.close()
        print("Cleanup complete.")


if __name__ == "__main__":
    main()
