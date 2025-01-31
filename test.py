import json
import logging
import re
import subprocess
import platform
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
DANGEROUS_KEYWORDS = ["rm", "format", "dd", "shutdown", ">", "&", ";", "sudo", "mkfs", "passwd"]

def detect_os():
    """Detect the operating system"""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    else:
        return "unknown"

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

def is_command_safe(command):
    """Improved safety check"""
    command_lower = command.lower()
    return not any(
        keyword in command_lower
        for keyword in DANGEROUS_KEYWORDS
    ) and not re.search(r"[$(){}\\<>]", command)

def sanitize_command(command):
    """Enhanced command sanitization"""
    # Remove code blocks and special characters
    command = re.sub(r"```.*?```", "", command, flags=re.DOTALL)
    command = re.sub(r"[;&`'\"{}()<>$]", "", command).strip()
    # Take only the first line and split on first non-command character
    return command.split("\n")[0].split("#")[0].split("//")[0]

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

def interpret_prompt(prompt):
    """Improved prompt handling with proper escaping"""
    try:
        with open("system_context.json", "r") as f:
            context = json.load(f)
    except FileNotFoundError:
        context = {}

    prompt_template = (
        f"Generate a terminal command for {context.get('os', 'unknown')} system. "
        f"User request: {prompt}\n"
        "Return ONLY THE COMMAND with no explanations or formatting."
    )

    try:
        result = subprocess.run(
            ['ollama', 'run', 'deepseek-coder', prompt_template],
            text=True,
            capture_output=True,
            timeout=10
        )
        return sanitize_command(result.stdout)
    except subprocess.TimeoutExpired:
        return "echo 'Error: Command generation timed out'"
    except Exception as e:
        return f"echo 'Error: {str(e)}'"

def execute_command(command):
    """Safer execution with better error handling"""
    if not command or command.startswith("echo 'Error"):
        return "Invalid command"

    if not is_command_safe(command):
        error_msg = f"Blocked potentially unsafe command: {command}"
        logging.error(error_msg)
        print(Fore.RED + error_msg)
        return error_msg

    try:
        logging.info(f"Executing: {command}")
        print(Fore.GREEN + f"Executing: {command}")
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            timeout=15
        )
        output = result.stdout if result.returncode == 0 else result.stderr
        print(Fore.BLUE + "Output:\n" + output)
        return output
    except subprocess.TimeoutExpired:
        error_msg = "Command timed out (15s)"
        logging.error(error_msg)
        print(Fore.RED + error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logging.error(error_msg)
        print(Fore.RED + error_msg)
        return error_msg

def main():
    print(Fore.YELLOW + "=== Smart Terminal Assistant ===")
    execute_context_commands()
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit"]:
                print(Fore.YELLOW + "Goodbye!")
                break
                
            command = interpret_prompt(user_input)
            execute_command(command)
            
        except KeyboardInterrupt:
            print(Fore.YELLOW + "\nOperation canceled by user.")
            break

if __name__ == "__main__":
    main()