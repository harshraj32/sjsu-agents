import subprocess
import logging
from colorama import Fore, Style, init
import re

# Initialize colorama for colorful terminal output
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agent_activity.log"),  # Log to a file
        logging.StreamHandler(),  # Log to the console
    ],
)

def sanitize_command(command):
    """
    Sanitizes the command by removing backticks and other unwanted characters.
    """
    # Remove backticks and leading/trailing whitespace
    command = re.sub(r"```bash|```|`", "", command).strip()
    return command

def interpret_prompt(prompt):
    """
    Interprets the user's prompt using Ollama's Code Llama model via API.
    """
    # Use this prompt template to ensure only commands are generated
    command_prompt = (
        f"Translate the following prompt into a terminal command and only that. "
        f"Do not include any explanations, descriptions, or additional text. Just provide the command:\n\n"
        f"{prompt}"
    )

    try:
        # Use Ollama's CLI to generate a response
        command = f'ollama run codellama "{command_prompt}"'
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        # Sanitize the command to remove unwanted characters
        sanitized_command = sanitize_command(result.stdout.strip())
        return sanitized_command
    except subprocess.CalledProcessError as e:
        return f"echo 'Error: Could not interpret prompt. {e.stderr}'"

def execute_command(command):
    """
    Executes the terminal command and returns the output or error.
    """
    try:
        logging.info(f"Executing command: {command}")
        print(Fore.GREEN + f"Executing: {command}")
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        logging.info(f"Command output:\n{result.stdout}")
        print(Fore.BLUE + "Output:")
        print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e.stderr}")
        print(Fore.RED + f"Error: {e.stderr}")
        return f"Error: {e.stderr}"

def main():
    print(Fore.YELLOW + "Welcome to the AI Terminal Agent!")
    print(Fore.YELLOW + "You can interact with the agent in the terminal.")

    # Terminal interaction loop
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print(Fore.YELLOW + "Goodbye!")
            break
        command = interpret_prompt(user_input)
        execute_command(command)

if __name__ == "__main__":
    main()