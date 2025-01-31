import getpass
import json
import logging
import platform
import re
import subprocess
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agent_activity.log"),
        logging.StreamHandler(),
    ],
)

CONTEXT_COMMANDS_FILE = "context_commands.txt"
MAX_RETRIES = 5
SAFE_COMMANDS = ['pwd', 'ls', 'echo', 'find', 'cd', 'cat', 'grep', 'curl', 'wget']

def detect_os():
    """Detect the operating system"""
    system = platform.system().lower()
    return {
        "darwin": "macos",
        "linux": "linux",
        "windows": "windows"
    }.get(system, "unknown")

def is_command_safe(command):
    """Enhanced safety check with command whitelisting"""
    # First check against dangerous patterns
    dangerous_patterns = [
        r"\brm\s+-[rf]|\brm\s+.*/",
        r"\bdd\s+if=.*",
        r"\bmkfs\b",
        r"\bpasswd\b",
        r"(\$\(|&\s*;|\\\s*;)",
        r">>\s+/\s*|>\s+/\s*"
    ]
    if any(re.search(p, command.lower()) for p in dangerous_patterns):
        return False
    
    # Then check for base command in whitelist
    base_cmd = command.split()[0].lower()
    return base_cmd in SAFE_COMMANDS

def sanitize_command(command):
    """More permissive sanitization for common commands"""
    # Remove code blocks and special characters
    command = re.sub(r"```.*?```", "", command, flags=re.DOTALL)
    command = re.sub(r"[;&`'\"{}<>|]", "", command).strip()
    
    # Extract first valid-looking command
    match = re.match(r"^[\w\/\.\-\$ ]+", command)
    return match.group(0).strip() if match else ""

def generate_command(prompt, context):
    """Improved command generation with safety priming"""
    prompt_template = (
        f"Generate a SINGLE SAFE terminal command for {context.get('os', 'unknown')} to: {prompt}\n"
        "Allowed commands: " + ", ".join(SAFE_COMMANDS) + "\n"
        "Return ONLY THE COMMAND with no explanations or formatting.\n"
        "Format: plain text without markdown or code blocks."
    )

    try:
        result = subprocess.run(
            ['ollama', 'run', 'deepseek-coder', prompt_template],
            text=True,
            capture_output=True,
            timeout=10
        )
        raw_command = result.stdout.strip()
        return sanitize_command(raw_command)
    except subprocess.TimeoutExpired:
        return "echo 'Error: Command generation timed out'"
    except Exception as e:
        return f"echo 'Error: {str(e)}'"

def execute_command(command):
    """Enhanced execution with privilege escalation handling"""
    if not command or not is_command_safe(command):
        return {
            "status": "error",
            "output": "Blocked unsafe/invalid command",
            "returncode": -1
        }

    try:
        # Handle sudo commands
        sudo_required = command.startswith('sudo') and not getpass.getuser() == "root"
        if sudo_required:
            print(Fore.YELLOW + "This command requires elevated privileges")
            sudo_password = getpass.getpass(Fore.YELLOW + "Enter sudo password: ")
            
        proc = subprocess.Popen(
            command,
            shell=True,
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        output, error = proc.communicate(
            input=f"{sudo_password}\n" if sudo_required else None,
            timeout=15
        )

        return {
            "status": "success" if proc.returncode == 0 else "error",
            "output": output or error,
            "returncode": proc.returncode,
            "command": command
        }
    except Exception as e:
        return {
            "status": "error",
            "output": str(e),
            "returncode": -1
        }

def analyze_results(original_prompt, command, output, returncode):
    """Smart analysis with safety awareness"""
    analysis_prompt = (
        f"Original request: {original_prompt}\n"
        f"Command attempted: {command}\n"
        f"Output received: {output}\n\n"
        "If this successfully answers the request, respond with 'SUCCESS'.\n"
        "If blocked by safety checks but command is actually safe, respond 'SAFE_OVERRIDE'.\n"
        "Otherwise suggest a NEW COMMAND from allowed list: " + ", ".join(SAFE_COMMANDS) + "\n"
        "Return ONLY: 'SUCCESS', 'SAFE_OVERRIDE', or the NEW COMMAND."
    )

    try:
        result = subprocess.run(
            ['ollama', 'run', 'deepseek-r1', analysis_prompt],
            text=True,
            capture_output=True,
            timeout=15
        )
        response = result.stdout.strip().upper()
        
        if "SUCCESS" in response:
            return "SUCCESS"
        elif "SAFE_OVERRIDE" in response:
            print(Fore.CYAN + "\nSafety override requested. Confirm execution:")
            confirm = input(Fore.YELLOW + "Run this command anyway? (y/n): ").lower()
            return command if confirm == 'y' else None
        else:
            return sanitize_command(result.stdout)
            
    except Exception:
        return None

def load_context_commands():
    """Load OS-specific context commands"""
    current_os = detect_os()
    try:
        with open(CONTEXT_COMMANDS_FILE, "r") as file:
            commands = []
            current_section = None
            for line in file:
                line = line.strip()
                if line.startswith("#"):
                    current_section = line[1:].strip().lower()
                elif current_section == current_os:
                    commands.append(line)
            return commands
    except FileNotFoundError:
        logging.error(f"Missing {CONTEXT_COMMANDS_FILE} file!")
        return []

# Rest of the functions remain the same as previous implementation
def execute_context_commands():
    """OS-aware context gathering"""
    commands = load_context_commands()
    context_data = {"os": detect_os()}

    print(Fore.CYAN + "\n=== Gathering System Context ===")
    for cmd in commands:
        if cmd and not cmd.startswith("#"):
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    text=True,
                    capture_output=True,
                    timeout=5
                )
                context_data[cmd] = result.stdout.strip()
                logging.info(f"Context command succeeded: {cmd}")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                error_msg = f"Error: {e.stderr}" if hasattr(e, "stderr") else "Timeout"
                context_data[cmd] = error_msg
                logging.error(f"Context command failed: {cmd} - {error_msg}")

    with open("system_context.json", "w") as f:
        json.dump(context_data, f, indent=2)
    print(Fore.CYAN + "=== System Context Saved ===\n")

def main():
    print(Fore.YELLOW + "=== Smart Terminal Assistant ===")
    execute_context_commands()
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                print(Fore.YELLOW + "Goodbye!")
                break

            # Load system context
            try:
                with open("system_context.json", "r") as f:
                    context = json.load(f)
            except FileNotFoundError:
                context = {}

            # Generate initial command
            command = generate_command(user_input, context)
            attempts = 0

            while attempts < MAX_RETRIES:
                # Execute command
                result = execute_command(command)
                print(Fore.CYAN + f"\nExecuted: {command}")
                print(Fore.BLUE + "Output:\n" + result['output'])

                # Analyze results
                analysis = analyze_results(
                    user_input,
                    command,
                    result['output'],
                    result['returncode']
                )

                if analysis == "SUCCESS":
                    print(Fore.GREEN + "\n✅ Task completed successfully!")
                    break
                elif analysis and analysis != command:
                    print(Fore.MAGENTA + f"\n🔄 Retrying with: {analysis}")
                    command = analysis
                    attempts += 1
                else:
                    print(Fore.RED + "\n❌ Maximum retries reached without success")
                    break

        except KeyboardInterrupt:
            print(Fore.YELLOW + "\nOperation canceled by user.")
            break

if __name__ == "__main__":
    main()