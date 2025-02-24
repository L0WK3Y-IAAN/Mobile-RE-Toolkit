#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Multi-threaded Androguard Control Flow Graph (CFG) Generator
# ---------------------------------------------------------------------------

import os
import subprocess
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress

console = Console()
OUTPUT_FOLDER = "src/output_folder"

# Ensure output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Function to find APKs in src and root folders
def find_apks():
    search_paths = [".", "src"]
    apks = []

    for path in search_paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.lower().endswith(".apk"):
                    apks.append(os.path.join(path, file))

    return sorted(apks)

# Function to extract available packages by decompiling APK
def extract_packages(apk_path):
    console.print(f"\n[cyan]🔍 Extracting package names from: {apk_path}[/]")

    try:
        # Run decompile to get package names
        process = subprocess.run(
            ["androguard", "decompile", "-o", OUTPUT_FOLDER, "-f", "png", apk_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Extract package names from the decompiled folder
        package_set = set()
        for root, _, files in os.walk(OUTPUT_FOLDER):
            for file in files:
                match = re.search(r'L([\w/]+);', file)
                if match:
                    package_name = match.group(1).split("/")[0]  # Extract top-level package
                    package_set.add(package_name)

        packages = sorted(package_set)
        if not packages:
            console.print("[red]❌ No packages found in APK![/]")
            return None

        return packages

    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Error extracting packages:\n{e.stderr}[/]")
        return None

# Multi-threaded function for extracting classes
def extract_classes(apk_path, package_name, progress, task):
    """Extracts the classes for a given package using Androguard"""
    try:
        process = subprocess.run(
            ["androguard", "decompile", "-o", OUTPUT_FOLDER, "-f", "png", "--limit", f"^L{package_name}/", apk_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if process.returncode == 0:
            console.print(f"[green]✅ Extracted classes for package: {package_name}[/]")
        else:
            console.print(f"[red]❌ Error extracting classes:\n{process.stderr}[/]")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Error extracting classes:\n{e.stderr}[/]")

    # Update the progress bar
    progress.update(task, advance=1)

# Multi-threaded function to extract CFG for selected package
def generate_cfg(apk_path, package_name):
    console.print(f"\n[cyan]🔗 Generating Control Flow Graph (CFG) for {package_name}...[/]")

    with Progress() as progress:
        task = progress.add_task("[cyan]Building CFG...[/]", total=1)

        # Using threads to extract classes
        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(extract_classes, apk_path, package_name, progress, task)

        console.print(f"[green]✅ CFG generated successfully! Check {OUTPUT_FOLDER} for output.[/]")

# Main execution
def main():
    console.print("\n[bold magenta]🔎 Multi-threaded Androguard CFG Generator 🔍[/]\n")

    # Find APKs
    apks = find_apks()
    if not apks:
        console.print("[red]❌ No APKs found! Place APKs in root or src/ folder.[/]")
        return

    # Display APKs for user selection
    table = Table(title="Detected APKs", show_header=True, header_style="bold magenta")
    table.add_column("Index", justify="center", style="cyan", no_wrap=True)
    table.add_column("APK File", style="green")

    for i, apk in enumerate(apks, 1):
        table.add_row(str(i), apk)

    console.print(table)

    # Select an APK
    while True:
        choice = Prompt.ask("[bold cyan]Enter the number of the APK to analyze[/]").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(apks):
            apk_path = apks[int(choice) - 1]
            break
        console.print("[red]⚠ Invalid selection. Try again.[/]")

    # Extract available packages
    packages = extract_packages(apk_path)
    if not packages:
        return

    # Display packages for user selection
    table = Table(title="Available Packages", show_header=True, header_style="bold magenta")
    table.add_column("Index", justify="center", style="cyan", no_wrap=True)
    table.add_column("Package Name", style="green")

    for i, package in enumerate(packages, 1):
        table.add_row(str(i), package)

    console.print(table)

    # Select a package
    while True:
        choice = Prompt.ask("[bold cyan]Enter the number of the package to analyze[/]").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(packages):
            package_name = packages[int(choice) - 1]
            break
        console.print("[red]⚠ Invalid selection. Try again.[/]")

    # Generate CFG
    generate_cfg(apk_path, package_name)

if __name__ == "__main__":
    main()
