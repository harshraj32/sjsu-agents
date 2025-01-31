import os
import random
import re
import subprocess
import sys
import time
from getpass import getpass

import pexpect


def request_interactive_session(username, password, port, use_gpu=False, retries=3):
    """Logs into the HPC, requests an interactive node, and starts Jupyter Notebook in one session."""
    command = "srun "
    if use_gpu:
        command += "-p gpu --gres=gpu "
    command += "--ntasks=1 --nodes=1 --cpus-per-task=4 --time=04:00:00 --pty /bin/bash"

    for attempt in range(retries):
        try:
            print(
                f"Attempt {attempt + 1}/{retries}: Connecting to HPC and requesting a node..."
            )
            child = pexpect.spawn(f"ssh {username}@coe-hpc1.sjsu.edu", timeout=30)
            child.logfile = sys.stdout.buffer  # Log output for debugging

            # Login
            child.expect(r"Password:")
            child.sendline(password)
            child.expect(r"\[.*@.* ~\]\$", timeout=30)  # Expect shell prompt
            print("✔ Successfully connected to the HPC login node.")

            # Request an interactive session
            child.sendline(command)
            time.sleep(5)  # Allow some time for allocation

            # Check if session is allocated
            print("🔄 Checking allocated node...")
            child.sendline("echo $SHELL")
            child.expect(
                r"\[.*@.* ~\]\$", timeout=20
            )  # Expect shell prompt after running the command

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
                else:
                    print("Still on the login node.")
            else:
                print("No valid node prompt detected.")

            time.sleep(5)
            # Load Python and start Jupyter Notebook
            print("🚀 Starting Jupyter Notebook...")
            child.sendline(
                f"module load python3; jupyter notebook --no-browser --port={port}"
            )
            child.expect(r"token=([\w\d]+)", timeout=50)  # Wait for token pattern

            # Extract the token directly from the matched output
            token = child.match.group(1).decode()  # Group 1 contains the token

            # Construct the Jupyter URL with the token
            jupyter_url = f"http://127.0.0.1:{port}/?token={token}"

            print(f"✔ Jupyter Notebook started at: {jupyter_url}")
            return node_name, jupyter_url, child

        except pexpect.exceptions.TIMEOUT as e:
            print(f"⏳ Attempt {attempt + 1} failed due to timeout: {e}")
            if attempt < retries - 1:
                time.sleep(5)
            else:
                print("❌ All attempts failed. Exiting...")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


def setup_jupyter(node_name, username, password, port):
    try:
        print(f"Connecting to node {node_name}...")
        password_prompt = f"Password:|{username}@'s Password:"
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


def setup_ssh_tunnel(username, password, node_name, port):
    """Sets up an SSH tunnel in two separate steps."""
    try:
        print(
            f"🔗 Step 1: Connecting to HPC login node ({username}@coe-hpc1.sjsu.edu)..."
        )
        child = pexpect.spawn(
            f"ssh -L {port}:localhost:{port} {username}@coe-hpc1.sjsu.edu", timeout=30
        )

        child.expect(r"Password:")
        child.sendline(password)
        child.expect(r"\[.*@.* ~\]\$", timeout=30)
        print("✔ Connected to login node.")

        print(f"🔗 Step 2: Connecting to compute node ({username}@{node_name})...")
        child.sendline(f"ssh -L {port}:localhost:{port} {username}@{node_name}")
        child.expect(r"\[.*@.* ~\]\$", timeout=30)
        print(f"✔ Connected to compute node: {node_name}")
        return child
    except Exception as e:
        print(f"❌ Error setting up SSH tunnel: {e}")
        sys.exit(1)


def main():
    print("SJSU HPC Jupyter Launcher\n")
    username = "017440488"
    if not username:
        print("Error: Username cannot be empty.")
        sys.exit(1)

    password = ""
    use_gpu = input("Require GPU? (y/n): ").lower().strip() == "y"
    port = random.randint(10000, 63999)

    print("Requesting compute resources...")
    node_name, jupyter_url, session = request_interactive_session(
        username, password, port, use_gpu
    )

    # print("Launching Jupyter Notebook...")
    # jupyter_url = setup_jupyter(node_name, username, password, port)

    print("Setting up SSH tunnel...")
    tunnel = setup_ssh_tunnel(username, password, node_name, port)

    print("\nSuccess! Use this URL in your browser:")
    print(jupyter_url)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nClosing connections...")
        tunnel.close()
        session.close()
        print("Cleanup complete.")


if __name__ == "__main__":
    main()
