#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Script by L0WK3Y
# https://github.com/L0WK3Y-IAAN
# ---------------------------------------------------------------------------

"""
Extracts strings from a decompiled APK or specified directory.

✅ Scans for APKs in the root & `src/` folder for user selection
✅ Automatically detects `apktool` using `shutil.which()`
✅ Recursively extracts printable ASCII strings from all files
✅ Uses **multi-threading** for parallel extraction
✅ Uses a **Rich** progress bar for better UX
✅ Stores output in `src/output/{APK_NAME}_EXTRACTION`
"""

import os
import re
import argparse
import csv
import subprocess
import shutil
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.progress import Progress

# Initialize rich console
console = Console()

# Auto-detect apktool
APKTOOL_PATH = shutil.which("apktool")

if not APKTOOL_PATH:
    console.print("[red]❌ apktool is not installed or not in PATH! Please install it and try again.[/]")
    sys.exit(1)

console.print(f"[green]✅ Using apktool at:[/] {APKTOOL_PATH}")

# Default output directory
OUTPUT_BASE_DIR = "src/output"

# Thread-safe results storage
results_lock = threading.Lock()
unique_results = set()


def find_apks():
    """Searches for APKs in the root and `src/` directories."""
    search_paths = [".", "src"]
    apks = []

    for path in search_paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.lower().endswith(".apk"):
                    apks.append(os.path.join(path, file))

    return apks


def select_apk():
    """Displays available APKs and allows the user to select one."""
    apks = find_apks()

    if not apks:
        console.print("[red]❌ No APKs found in the root or `src/` directories![/]")
        sys.exit(1)

    console.print("\n[cyan]📦 Available APKs:[/]")
    for i, apk in enumerate(apks, start=1):
        console.print(f"  [bold cyan][{i}][/bold cyan] {apk}")

    while True:
        choice = input("\n🔹 Select an APK by number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(apks):
            return apks[int(choice) - 1]
        console.print("[yellow]⚠ Invalid selection. Please enter a valid number.[/]")


def extract_strings_from_file(file_path, min_length=4):
    """
    Extract printable ASCII strings from a file.

    Args:
        file_path (str): Path to the file.
        min_length (int): Minimum length of string to extract.

    Returns:
        list of tuple: Each tuple contains (file_path, string) for every match.
    """
    results = []
    pattern = re.compile(r'[\x20-\x7E]{' + str(min_length) + r',}')

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            matches = pattern.findall(content)
            for match in matches:
                results.append((file_path, match))
    except Exception as e:
        console.print(f"[yellow]⚠ Error processing file {file_path}: {e}[/]")

    return results


def decompile_apk(apk_path):
    """
    Uses apktool to decompile the given APK into an output directory.

    Args:
        apk_path (str): Path to the APK file.

    Returns:
        str: Path to the decompiled directory.
    """
    apk_name = os.path.basename(apk_path).replace(".apk", "")
    output_dir = os.path.join(OUTPUT_BASE_DIR, f"{apk_name}_EXTRACTION")

    if os.path.exists(output_dir):
        console.print(f"[blue]📂 Removing existing directory:[/] {output_dir}")
        subprocess.run(f'rmdir /s /q "{output_dir}"', shell=True, check=True)

    console.print(f"[cyan]🔍 Decompiling APK:[/] {apk_path} -> {output_dir}")

    try:
        subprocess.run([APKTOOL_PATH, "d", "-f", apk_path, "-o", output_dir], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Error decompiling APK: {e}[/]")
        return None

    return output_dir


def process_file(file_path, min_length, task, progress):
    """
    Extracts strings from a single file and updates results.
    
    Args:
        file_path (str): Path to the file.
        min_length (int): Minimum length of string to extract.
        task: Progress bar task.
        progress: Rich progress bar instance.
    """
    extracted = extract_strings_from_file(file_path, min_length=min_length)

    # Store results in a thread-safe way
    with results_lock:
        unique_results.update(extracted)

    # Update progress
    progress.update(task, advance=1)


def process_directory(directory, min_length):
    """
    Recursively extracts strings from files in a directory using multi-threading and a Rich progress bar.

    Args:
        directory (str): Directory to scan.
        min_length (int): Minimum length of string to extract.

    Returns:
        list: Extracted strings.
    """
    all_files = [os.path.join(root, file) for root, _, files in os.walk(directory) for file in files]

    console.print(f"[magenta]📑 Extracting strings from:[/] {directory}")

    with Progress() as progress:
        task = progress.add_task("[cyan]Extracting Strings...", total=len(all_files))

        with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust the number of threads as needed
            for file_path in all_files:
                executor.submit(process_file, file_path, min_length, task, progress)

    return sorted(unique_results, key=lambda x: (x[0], x[1]))


def main():
    parser = argparse.ArgumentParser(
        description="Extract printable strings from a decompiled APK or directory."
    )
    parser.add_argument("input", nargs="?", help="APK file or directory (optional, will scan if not provided)")
    parser.add_argument("-m", "--min-length", type=int, default=4,
                        help="Minimum string length to extract (default: 4)")
    args = parser.parse_args()

    input_path = args.input
    min_length = args.min_length

    # If no input provided, scan for APKs and allow selection
    if not input_path:
        input_path = select_apk()

    if not os.path.exists(input_path):
        console.print(f"[red]❌ Error: {input_path} does not exist.[/]")
        return

    # If input is an APK, decompile it
    if input_path.endswith(".apk"):
        output_dir = decompile_apk(input_path)
        if not output_dir:
            console.print("[red]❌ APK decompilation failed. Exiting...[/]")
            return
    else:
        output_dir = input_path

    # Extract strings with multi-threading and progress bar
    extracted_strings = process_directory(output_dir, min_length)

    # Save to output file
    apk_name = os.path.basename(output_dir)
    output_file = os.path.join(output_dir, f"{apk_name}_strings.csv")

    try:
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["file", "string"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for file_path, string in extracted_strings:
                writer.writerow({"file": file_path, "string": string})

        console.print(f"\n[green]✅ Extracted strings saved to:[/] {output_file}")
    except Exception as e:
        console.print(f"[red]❌ Error writing to output file: {e}[/]")


if __name__ == "__main__":
    main()
