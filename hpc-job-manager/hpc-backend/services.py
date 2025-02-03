import random
import re
import signal
import sys
import threading
import time

import pexpect


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
        self.running = True
        self.jupyter_ready = threading.Event()

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle cleanup on shutdown signals"""
        print("\n🛑 Shutting down gracefully...")
        self.running = False
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        """Clean up resources"""
        if self.session:
            self.session.close()
        if self.tunnel:
            self.tunnel.close()

    def request_interactive_session(self):
        """Logs into HPC, requests a node, and starts Jupyter Notebook."""
        command = f"srun --ntasks={self.num_tasks} --nodes={self.num_nodes} --cpus-per-task=4 --time={self.cpu_time} --pty /bin/bash"

        try:
            print("🔗 Connecting to HPC and requesting a node...")
            self.session = pexpect.spawn(
                f"ssh {self.username}@coe-hpc1.sjsu.edu", timeout=30
            )

            index = self.session.expect(["Password:", pexpect.EOF, pexpect.TIMEOUT])
            if index == 0:
                self.session.sendline(self.password)
            elif index == 1:
                raise Exception("Unexpected EOF received during SSH")
            elif index == 2:
                raise Exception("SSH connection timed out")

            self.session.expect(r"\[.*@.* ~\]\$", timeout=30)
            print("✔ Successfully connected to HPC.")
            self.session.sendline(command)
            time.sleep(5)

            print("🔄 Checking allocated node...")
            self.session.sendline("echo $SHELL")
            self.session.expect(r"\[.*@.* ~\]\$", timeout=20)

            shell_output = self.session.before.decode()
            raw_prompt = self.session.after.decode()

            print(f"Shell output: {shell_output}")
            print(f"Detected prompt: {raw_prompt}")

            self.session.sendline("hostname")
            self.session.expect(r"(\w+)", timeout=20)

            match = re.search(r"@(\w+)", raw_prompt)
            if match:
                self.node_name = match.group(1)
                if self.node_name != "coe-hpc1":
                    print(f"Interactive session allocated. Node: {self.node_name}")
                else:
                    print("Still on the login node.")
            else:
                print("No valid node prompt detected.")

            if self.node_name == "coe-hpc1":
                print("❌ Error: Allocation failed. Still on the login node.")
                return False, None

            time.sleep(5)
            print(f"🚀 Starting Jupyter Notebook on {self.node_name}...")
            self.session.sendline(
                f"module load python3; jupyter notebook --no-browser --port={self.port}"
            )

            # Look for Jupyter URL pattern
            index = self.session.expect(
                [
                    r"http://localhost:\d+/\?token=([\w\d]+)",
                    r"token=([\w\d]+)",
                    pexpect.TIMEOUT,
                ],
                timeout=30,
            )

            if index in [0, 1]:
                token = self.session.match.group(1).decode()
                self.jupyter_url = f"http://127.0.0.1:{self.port}/?token={token}"
                print(f"✨ Jupyter URL: {self.jupyter_url}")
                self.jupyter_ready.set()
            else:
                print("❌ Failed to get Jupyter token")
                return False, None

            # Keep the session alive
            while self.running:
                self.session.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=30)
                if not self.running:
                    break
                time.sleep(1)

            return True, self.jupyter_url

        except Exception as e:
            print(f"❌ Error: {e}")
            return False, None

    def setup_ssh_tunnel(self):
        """Sets up a persistent SSH tunnel."""
        try:
            print("🔗 Setting up SSH tunnel to login node...")
            self.tunnel = pexpect.spawn(
                f"ssh -L {self.port}:localhost:{self.port} {self.username}@coe-hpc1.sjsu.edu",
                timeout=30,
            )

            self.tunnel.expect(r"Password:")
            self.tunnel.sendline(self.password)
            self.tunnel.expect(r"\[.*@.* ~\]\$", timeout=30)
            print("✔ Connected to login node.")

            print(f"🔗 Forwarding port to compute node: {self.node_name}...")
            self.tunnel.sendline(
                f"ssh -L {self.port}:localhost:{self.port} {self.username}@{self.node_name}"
            )
            self.tunnel.expect(r"\[.*@.* ~\]\$", timeout=30)
            print(f"✔ SSH tunnel established to {self.node_name}")

            # Keep the tunnel alive
            while self.running:
                self.tunnel.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=30)
                if not self.running:
                    break
                time.sleep(1)

            return True
        except Exception as e:
            print(f"❌ SSH Tunnel Error: {e}")
            return False

    def start(self):
        """Handles the entire flow in separate threads."""

        def session_wrapper():
            success, jupyter_url = self.request_interactive_session()
            if not success:
                print("❌ Failed to start Jupyter Notebook.")
                self.running = False

        def tunnel_wrapper():
            success = self.setup_ssh_tunnel()
            if not success:
                print("❌ Failed to establish SSH tunnel.")
                self.running = False

        # Create threads for session and SSH tunnel setup
        session_thread = threading.Thread(target=session_wrapper, daemon=True)
        session_thread.start()

        # Wait for initial setup to complete
        time.sleep(10)

        # Proceed to tunnel setup if the session was successful
        if self.node_name:
            tunnel_thread = threading.Thread(target=tunnel_wrapper, daemon=True)
            tunnel_thread.start()

            try:
                # Wait for Jupyter URL to be ready
                if self.jupyter_ready.wait(
                    timeout=60
                ):  # Wait up to 60 seconds for Jupyter to start
                    print(f"🎉 Setup complete! Jupyter URL: {self.jupyter_url}")
                    return True, self.jupyter_url
                else:
                    print("❌ Timeout waiting for Jupyter URL")
                    return False, None

            except KeyboardInterrupt:
                self.signal_handler(signal.SIGINT, None)

        return False, None

    def get_jupyter_url(self):
        """Get the current Jupyter URL."""
        return self.jupyter_url if self.jupyter_ready.is_set() else None


class HPCJobMonitor:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.running = True
        self.jobs = []
        self.jobs_lock = threading.Lock()
        self.monitor_thread = None
        self.callback = None

    def start_monitoring(self, update_callback):
        """Start background job monitoring thread"""
        self.callback = update_callback
        self.monitor_thread = threading.Thread(target=self._monitor_jobs, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()

    def _monitor_jobs(self):
        """Background thread that periodically checks for running jobs"""
        while self.running:
            try:
                current_jobs = self._fetch_jobs()
                with self.jobs_lock:
                    self.jobs = current_jobs.copy()
                if self.callback:
                    self.callback(current_jobs)
            except Exception as e:
                print(f"Job monitoring error: {e}")
            time.sleep(30)  # Update every 30 seconds

    def _fetch_jobs(self):
        """Connect to HPC and fetch running jobs"""
        try:
            session = pexpect.spawn(
                f"ssh {self.username}@coe-hpc1.sjsu.edu", timeout=30
            )
            session.expect("Password:")
            session.sendline(self.password)
            session.expect(r"\[.*@.* ~\]\$", timeout=30)

            session.sendline(f"squeue -u {self.username} --Format=JobID:10,Partition:10,Name:30,User:10,State:10,TimeUsed:10,NNodes:10,NodeList:30")
            session.expect(r"\[.*@.* ~\]\$", timeout=30)

            output = session.before.decode().split("\n")
            jobs = []

            # Skip header line and process job entries
            for line in output[1:]:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 8:
                        job = {
                            "job_id": parts[0],
                            "partition": parts[1],
                            "name": parts[2],
                            "user": parts[3],
                            "status": parts[4],
                            "time": parts[5],
                            "nodes": parts[6],
                            "nodelist": parts[7],
                        }
                        jobs.append(job)

            session.close()
            return jobs

        except Exception as e:
            print(f"Error fetching jobs: {e}")
            return []

    def cancel_job(self, job_id):
        """Cancel a specific job"""
        try:
            session = pexpect.spawn(
                f"ssh {self.username}@coe-hpc1.sjsu.edu", timeout=30
            )
            session.expect("Password:")
            session.sendline(self.password)
            session.expect(r"\[.*@.* ~\]\$", timeout=30)

            session.sendline(f"scancel {job_id}")
            session.expect(r"\[.*@.* ~\]\$", timeout=30)
            session.close()

            return True
        except Exception as e:
            print(f"Error canceling job {job_id}: {e}")
            return False

    def get_current_jobs(self):
        """Return the current list of jobs"""
        with self.jobs_lock:
            return self.jobs.copy()
