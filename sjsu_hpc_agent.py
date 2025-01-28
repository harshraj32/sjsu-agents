import os
import sys
import re
import random
import paramiko
import pexpect
import requests
from getpass import getpass
import subprocess
import time

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = "sk-80a6ba9554324cffbecd4b8ea45b4274"

def query_deepseek(prompt):
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(DEEPSEEK_API_URL, json=data, headers=headers)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Error querying DeepSeek: {str(e)}"

def request_interactive_session(username, password, use_gpu=False):
    command = "srun "
    if use_gpu:
        command += "-p gpu --gres=gpu "
    command += "--ntasks=1 --nodes=1 --cpus-per-task=4 --time=04:00:00 --pty /bin/bash"
    
    try:
        child = pexpect.spawn(f'ssh {username}@coe-hpc1.sjsu.edu', timeout=30)
        child.expect('password:')
        child.sendline(password)
        child.expect(r'\$')  # Wait for shell prompt
        child.sendline(command)
        # Expect node prompt (adjust regex based on your cluster's prompt)
        child.expect(r'(\w+-\d+)')  # Example for node name like 'gpu-001'
        node_name = child.match.group(1)
        return node_name, child
    except pexpect.exceptions.TIMEOUT:
        error = "Timeout while waiting for node allocation."
        suggestion = query_deepseek(error)
        print(f"Error: {error}\nDeepSeek: {suggestion}")
        sys.exit(1)
    except Exception as e:
        error = f"Failed to start interactive session: {str(e)}"
        suggestion = query_deepseek(error)
        print(f"Error: {error}\nDeepSeek: {suggestion}")
        sys.exit(1)

def setup_jupyter(node_name, username, password, port):
    try:
        child = pexpect.spawn(f'ssh {username}@{node_name}', timeout=30)
        child.expect('password:')
        child.sendline(password)
        child.expect(r'\$')
        child.sendline(f'module load python3; jupyter notebook --no-browser --port={port}')
        time.sleep(2)
        child.expect(r'http://localhost:\d+/\?token=\w+')
        jupyter_url = child.match.group(0)
        return jupyter_url.replace('localhost', '127.0.0.1')
    except pexpect.exceptions.TIMEOUT:
        error = "Timeout starting Jupyter."
        suggestion = query_deepseek(error)
        print(f"Error: {error}\nDeepSeek: {suggestion}")
        sys.exit(1)
    except Exception as e:
        error = f"Failed to start Jupyter: {str(e)}"
        suggestion = query_deepseek(error)
        print(f"Error: {error}\nDeepSeek: {suggestion}")
        sys.exit(1)

def setup_ssh_tunnel(username, node_name, port):
    try:
        tunnel = subprocess.Popen([
            'ssh', '-o', 'StrictHostKeyChecking=no',
            '-L', f'{port}:localhost:{port}',
            '-J', f'{username}@coe-hpc1.sjsu.edu',
            f'{username}@{node_name}', '-N'
        ])
        return tunnel
    except Exception as e:
        error = f"Tunnel setup failed: {str(e)}"
        suggestion = query_deepseek(error)
        print(f"Error: {error}\nDeepSeek: {suggestion}")
        sys.exit(1)

def main():
    print("SJSU HPC Jupyter Launcher\n")
    username = input("SJSU ID: ").strip()
    password = getpass("SJSU Password: ")
    use_gpu = input("Require GPU? (y/n): ").lower().strip() == 'y'
    port = random.randint(10000, 63999)
    
    print("Requesting compute resources...")
    node_name, session = request_interactive_session(username, password, use_gpu)
    print(f"Allocated node: {node_name}")
    
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