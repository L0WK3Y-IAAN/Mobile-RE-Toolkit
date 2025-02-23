#!/usr/bin/env python3
"""
main_menu.py

Updated version that:
1) Prints an ASCII banner and a menu of scripts in "./scripts".
2) Runs the chosen script in a subprocess.
3) If Ctrl+C (KeyboardInterrupt) happens during that subprocess run, 
   we catch it and return to the menu rather than killing the entire Python process.
"""

import os
import sys
import subprocess

os.system('cls' if os.name == 'nt' else 'clear')

try:
    from colorama import init, Fore, Style
except ImportError:
    print("Please install colorama: pip install colorama")
    sys.exit(1)

init(autoreset=True)

BANNER = r"""
███╗   ███╗   ██████╗    ███████╗████████╗
████╗ ████║   ██╔══██╗   ██╔════╝╚══██╔══╝
██╔████╔██║   ██████╔╝   █████╗     ██║   
██║╚██╔╝██║   ██╔══██╗   ██╔══╝     ██║   
██║ ╚═╝ ██║██╗██║  ██║██╗███████╗██╗██║   
╚═╝     ╚═╝╚═╝╚═╝  ╚═╝╚═╝╚══════╝╚═╝╚═╝   
""".strip("\n")

SCRIPT_DIR = "./scripts"

def prettify_script_name(filename: str) -> str:
    """Remove '.py', replace underscores with spaces, and capitalize each word."""
    if filename.endswith(".py"):
        filename = filename[:-3]
    filename = filename.replace("_", " ")
    words = filename.split()
    capitalized_words = [w.capitalize() for w in words]
    return " ".join(capitalized_words)

def main():
    if not os.path.isdir(SCRIPT_DIR):
        print(f"{Fore.RED}[-] 'scripts' folder not found at: {SCRIPT_DIR}{Style.RESET_ALL}")
        sys.exit(1)

    # Gather a list of *.py files in the scripts directory
    scripts = sorted(f for f in os.listdir(SCRIPT_DIR) if f.endswith(".py"))
    if not scripts:
        print(f"{Fore.RED}[-] No Python scripts found in {SCRIPT_DIR}{Style.RESET_ALL}")
        sys.exit(1)

    while True:
        # Print banner & menu
        print(f"{Fore.RED}{Style.DIM}{BANNER}{Style.RESET_ALL}\n")
        print(f"{Fore.MAGENTA}{Style.BRIGHT}Select a script to run:{Style.RESET_ALL}")
        for i, script_name in enumerate(scripts, start=1):
            display_name = prettify_script_name(script_name)
            print(f"{Fore.GREEN}[{i}] {display_name}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[Q] Quit{Style.RESET_ALL}")

        choice = input(f"{Fore.CYAN}\nEnter choice: {Style.RESET_ALL}").strip().lower()
        if choice == "q":
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"{Fore.CYAN}Goodbye!{Style.RESET_ALL}")
            break

        if not choice.isdigit():
            print(f"{Fore.RED}[!] Invalid input. Please enter a number or Q.{Style.RESET_ALL}")
            continue

        idx = int(choice)
        if 1 <= idx <= len(scripts):
            script_to_run = scripts[idx - 1]
            full_path = os.path.join(SCRIPT_DIR, script_to_run)

            print(f"{Fore.CYAN}[*] Running script:{Style.RESET_ALL} {full_path}\n")
            # --------------------------------------------------------
            # KEY CHANGE: Catch KeyboardInterrupt so we return to menu
            # --------------------------------------------------------
            try:
                subprocess.run(["python", full_path], check=True)
            except KeyboardInterrupt:
                print(f"{Fore.YELLOW}\n[!] Sub-script interrupted by user. Returning to menu...{Style.RESET_ALL}")
                # We 'continue' so the while loop re-displays the banner/menu
                continue
            except subprocess.CalledProcessError as e:
                print(f"{Fore.RED}[-] Script returned an error (exit code {e.returncode}).{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}[!] Invalid selection.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
