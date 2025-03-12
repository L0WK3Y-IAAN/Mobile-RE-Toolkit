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
✅ Scans for 'WIP' scripts and adds their **directories** to .gitignore.
"""

import os
import sys
import re
import subprocess
from rich.console import Console
from rich.table import Table
from rich import box
from rich.prompt import Prompt
import shutil  # For moving files

# Initialize rich console
console = Console()

# Paths
SCRIPT_DIR = "./scripts"
GITIGNORE_PATH = "./.gitignore"

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

def get_description_from_readme(folder_path: str) -> str:
    """
    Reads the first '**...**' occurrence in a README.md file
    and returns that text. If no README or no match, return fallback.
    """
    readme_path = os.path.join(folder_path, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Look for the first occurrence of text within **...**
        match = re.search(r"\*\*(.*?)\*\*", content)
        if match:
            return match.group(1).strip()
    return "No description found"

def scan_wip_script_dirs():
    """Scans for scripts containing 'WIP' in the filename and adds their parent directories to .gitignore."""
    wip_dirs = set()

    if not os.path.isdir(SCRIPT_DIR):
        return

    for root, _, files in os.walk(SCRIPT_DIR):
        for file in files:
            if "WIP" in file and file.endswith(".py"):  # Identify WIP scripts
                wip_dirs.add(os.path.relpath(root))  # Store the directory

    if wip_dirs:
        console.print(f"[yellow]⚠ Found {len(wip_dirs)} WIP script directories. Adding to .gitignore...[/]")

        # Ensure .gitignore exists
        if not os.path.exists(GITIGNORE_PATH):
            with open(GITIGNORE_PATH, "w") as f:
                f.write("# Git Ignore File\n")

        # Read existing .gitignore
        with open(GITIGNORE_PATH, "r") as f:
            gitignore_lines = set(f.read().splitlines())

        # Add missing WIP directories
        new_entries = [directory for directory in wip_dirs if directory not in gitignore_lines]
        if new_entries:
            with open(GITIGNORE_PATH, "a") as f:
                f.write("\n# Auto-added WIP script directories\n")
                f.write("\n".join(new_entries) + "\n")
            console.print("[green]✅ Updated .gitignore with WIP script directories.[/]")
        else:
            console.print("[green]✅ All WIP directories are already in .gitignore.[/]")
    else:
        console.print("[cyan]🔍 No WIP scripts found.[/]")

def organize_scripts():
    """Moves scripts into subfolders based on their filenames."""
    if not os.path.isdir(SCRIPT_DIR):
        os.makedirs(SCRIPT_DIR)

    for filename in os.listdir(SCRIPT_DIR):
        file_path = os.path.join(SCRIPT_DIR, filename)

        if filename.endswith(".py") and os.path.isfile(file_path):
            script_name = prettify_script_name(filename)
            dest_folder = os.path.join(SCRIPT_DIR, script_name)
            dest_path = os.path.join(dest_folder, filename)

            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)

            if file_path != dest_path:  
                shutil.move(file_path, dest_path)
                console.print(f"[green]📂 Moved:[/] {filename} → {dest_folder}/")

def list_scripts():
    """Returns a sorted list of Python scripts from subdirectories."""
    if not os.path.isdir(SCRIPT_DIR):
        console.print(f"[bold red]❌ Error:[/] 'scripts' folder not found: {SCRIPT_DIR}")
        input("Press Enter to continue...")
        sys.exit(1)

    scripts = []
    for root, _, files in os.walk(SCRIPT_DIR):
        for file in files:
            if file.endswith(".py"):
                scripts.append(os.path.join(root, file))

    scripts.sort()
    if not scripts:
        console.print(f"[bold red]❌ Error:[/] No Python scripts found in {SCRIPT_DIR}")
        input("Press Enter to continue...")
        sys.exit(1)

    return scripts

def display_menu(scripts):
    """Displays the script selection menu with a rich table."""
    os.system("cls" if os.name == "nt" else "clear")
    console.print(f"[bold magenta]{BANNER}[/]\n")

    # Enable row lines (show_lines=True) and change box style if you like
    table = Table(
        title="📜 Available Scripts",
        show_header=True,
        header_style="bold magenta",
        show_lines=True,               # <-- key to add a line between rows
        box=box.SIMPLE_HEAVY           # <-- optional: pick a nicer border style
    )
    table.add_column("Index", justify="center", style="cyan", no_wrap=True)
    table.add_column("Script Name", style="green")
    table.add_column("Description", style="yellow")

    for i, script_path in enumerate(scripts, 1):
        script_name = prettify_script_name(os.path.basename(script_path))
        folder_path = os.path.dirname(script_path)
        description = get_description_from_readme(folder_path)
        table.add_row(str(i), script_name, description)

    console.print(table)
    console.print("[bold yellow][Q] Quit[/]\n")

def main():
    """Main script loop to display menu and execute selected scripts."""
    organize_scripts()
    scan_wip_script_dirs()  # Scan for WIP script directories and update .gitignore
    scripts = list_scripts()

    try:
        while True:
            display_menu(scripts)

            user_input = Prompt.ask("[bold cyan]Enter choice and arguments (ex: 2 -o output)[/]", default="Q").strip()

            if user_input.lower() == "q":
                os.system("cls" if os.name == "nt" else "clear")
                console.print("[bold cyan]👋 Goodbye![/]")
                break

            parts = user_input.split()
            if not parts or not parts[0].isdigit():
                console.print("[bold red]⚠ Invalid input. Please enter a valid number followed by optional arguments.[/]")
                input("Press Enter to continue...")
                continue

            script_index = int(parts[0])
            script_args = parts[1:]

            if not (1 <= script_index <= len(scripts)):
                console.print("[bold red]⚠ Invalid selection. Please enter a valid number.[/]")
                input("Press Enter to continue...")
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