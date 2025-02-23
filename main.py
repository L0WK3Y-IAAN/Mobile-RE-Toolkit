#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Script by L0WK3Y
# https://github.com/L0WK3Y-IAAN
# ---------------------------------------------------------------------------

"""
main_menu.py

Modernized version that:
✅ Uses `rich` for better UI.
✅ Organizes scripts into folders based on file names.
✅ Lists Python scripts from "./scripts" with a table.
✅ Supports passing arguments with script selection (ex: "3 -o output ./file").
✅ Runs scripts in subprocesses, handling KeyboardInterrupts safely.
"""

import os
import sys
import subprocess
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
import shutil  # For moving files

# Initialize rich console
console = Console()

# Path to scripts folder
SCRIPT_DIR = "./scripts"

# Banner
BANNER = r"""
███╗   ███╗   ██████╗    ███████╗████████╗
████╗ ████║   ██╔══██╗   ██╔════╝╚══██╔══╝
██╔████╔██║   ██████╔╝   █████╗     ██║   
██║╚██╔╝██║   ██╔══██╗   ██╔══╝     ██║   
██║ ╚═╝ ██║██╗██║  ██║██╗███████╗██╗██║   
╚═╝     ╚═╝╚═╝╚═╝  ╚═╝╚══════╝╚═╝╚═╝   
""".strip("\n")

def prettify_script_name(filename: str) -> str:
    """Removes '.py', replaces underscores with spaces, and capitalizes each word."""
    return filename.replace("_", " ").replace(".py", "").title()

def organize_scripts():
    """
    Moves scripts in the 'scripts' folder into subfolders based on their filenames.
    Example: 'example_script.py' -> 'scripts/Example Script/example_script.py'
    """
    if not os.path.isdir(SCRIPT_DIR):
        os.makedirs(SCRIPT_DIR)  # Ensure the scripts folder exists

    for filename in os.listdir(SCRIPT_DIR):
        file_path = os.path.join(SCRIPT_DIR, filename)

        if filename.endswith(".py") and os.path.isfile(file_path):
            script_name = prettify_script_name(filename)  # Convert script name
            dest_folder = os.path.join(SCRIPT_DIR, script_name)
            dest_path = os.path.join(dest_folder, filename)

            # Move script if it's not already inside the correct folder
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)  # Create the folder if it doesn't exist
            
            if file_path != dest_path:  # Avoid moving files already in place
                shutil.move(file_path, dest_path)
                console.print(f"[green]📂 Moved:[/] {filename} → {dest_folder}/")

def list_scripts():
    """
    Returns a sorted list of Python scripts from subdirectories within SCRIPT_DIR.
    """
    if not os.path.isdir(SCRIPT_DIR):
        console.print(f"[bold red]❌ Error:[/] 'scripts' folder not found: {SCRIPT_DIR}")
        input("Press Enter to continue...")
        sys.exit(1)

    scripts = []
    for root, _, files in os.walk(SCRIPT_DIR):
        for file in files:
            if file.endswith(".py"):
                scripts.append(os.path.join(root, file))

    scripts.sort()  # Sort alphabetically
    if not scripts:
        console.print(f"[bold red]❌ Error:[/] No Python scripts found in {SCRIPT_DIR}")
        input("Press Enter to continue...")
        sys.exit(1)

    return scripts

def display_menu(scripts):
    """Displays the script selection menu with a rich table."""
    os.system("cls" if os.name == "nt" else "clear")  # Clear screen
    console.print(f"[bold magenta]{BANNER}[/]\n")

    table = Table(title="📜 Available Scripts", show_header=True, header_style="bold magenta")
    table.add_column("Index", justify="center", style="cyan", no_wrap=True)
    table.add_column("Script Name", style="green")
    table.add_column("Location", style="yellow")

    for i, script_path in enumerate(scripts, 1):
        script_name = prettify_script_name(os.path.basename(script_path))
        script_folder = os.path.basename(os.path.dirname(script_path))
        table.add_row(str(i), script_name, script_folder)

    console.print(table)
    console.print("[bold yellow][Q] Quit[/]\n")

def main():
    """Main script loop to display menu and execute selected scripts."""
    organize_scripts()  # Ensure scripts are sorted into folders before running
    scripts = list_scripts()

    try:
        while True:
            display_menu(scripts)

            # Prompt user for input (allows extra arguments)
            user_input = Prompt.ask("[bold cyan]Enter choice and arguments (ex: 2 -o output)[/]", default="Q").strip()

            if user_input.lower() == "q":
                os.system("cls" if os.name == "nt" else "clear")  # Clear screen
                console.print("[bold cyan]👋 Goodbye![/]")
                break

            # Split input into parts: first part is the script number, the rest are args
            parts = user_input.split()
            if not parts or not parts[0].isdigit():
                console.print("[bold red]⚠ Invalid input. Please enter a valid number followed by optional arguments.[/]")
                input("Press Enter to continue...")
                continue

            script_index = int(parts[0])  # Extract script index
            script_args = parts[1:]  # Extract additional arguments

            if not (1 <= script_index <= len(scripts)):
                console.print("[bold red]⚠ Invalid selection. Please enter a valid number.[/]")
                continue

            script_to_run = scripts[script_index - 1]

            console.print(f"[bold cyan]▶ Running script:[/] {script_to_run} [yellow]{' '.join(script_args)}[/]\n")

            try:
                subprocess.run(["python", script_to_run] + script_args, check=True)
            except KeyboardInterrupt:
                console.print("\n[bold yellow]⚠ Script interrupted. Returning to menu...[/]")
            except subprocess.CalledProcessError as e:
                console.print(f"[bold red]❌ Error:[/] Script exited with code {e.returncode}.")
                input("Press Enter to continue...")

    except KeyboardInterrupt:
        os.system("cls" if os.name == "nt" else "clear")
        console.print("\n[bold yellow]👋 Goodbye![/]")

if __name__ == "__main__":
    main()
