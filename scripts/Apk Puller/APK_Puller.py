#!/usr/bin/env python3
import argparse
import subprocess
import os
from rich.console import Console
from rich.table import Table
import concurrent.futures

console = Console()
OUTPUT_DIR = "src/output/pulled_apks"

def list_packages(exclude_system: bool, filter_system: bool):
    """
    List packages installed on the device.
    Uses adb shell pm list packages.
    If exclude_system is True, only third-party packages are listed.
    If filter_system is True, filters out known system packages like 'com.google', 'com.android'.
    """
    try:
        cmd = ["adb", "shell", "pm", "list", "packages", "-3"] if exclude_system else ["adb", "shell", "pm", "list", "packages", "-a"]
        output = subprocess.check_output(cmd, text=True)

        packages = [line.replace("package:", "").strip() for line in output.splitlines()]

        # Define system prefixes to filter out
        system_prefixes = ("com.google", "com.android", "androidx", "com.qualcomm", "com.samsung", "android")

        if filter_system:
            packages = [pkg for pkg in packages if not pkg.startswith(system_prefixes)]

        return packages
    except subprocess.CalledProcessError as e:
        console.print("[red]Error listing packages:[/red]", e)
        return []

def get_apk_path(package: str):
    """
    Retrieve the APK file path for the given package.
    """
    try:
        cmd = ["adb", "shell", "pm", "path", package]
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
        if not output:
            console.print(f"[yellow]⚠ No APK path found for {package} (may be a system app or hidden).[/]")
            return None
        for line in output.splitlines():
            if line.startswith("package:"):
                return line.replace("package:", "").strip()
    except subprocess.CalledProcessError:
        console.print(f"[red]⚠ Error retrieving APK path for {package} (may require root).[/]")
    return None

def pull_apk(apk_path, package_name):
    """Pull the APK from the device and save it to the output directory."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    apk_filename = f"{package_name}.apk"
    output_path = os.path.join(OUTPUT_DIR, apk_filename)

    console.print(f"[cyan]📦 Pulling APK: {package_name} -> {output_path}[/]")
    result = subprocess.run(["adb", "pull", apk_path, output_path], capture_output=True, text=True)

    if result.returncode == 0:
        console.print(f"[green]✔ Successfully pulled {apk_filename} to {OUTPUT_DIR}[/]")
    else:
        console.print(f"[red]❌ Failed to pull {package_name}: {result.stderr}[/]")

def main():
    parser = argparse.ArgumentParser(description="List APKs from an Android device")
    parser.add_argument("--exclude-system", action="store_true", 
                        help="Exclude system/default packages (only list third-party apps)")
    
    filter_system_prompt = console.input("[bold cyan]Would you like to filter out system-related packages (com.google, com.android, etc.)? (y/N): [/]")
    filter_system = filter_system_prompt.strip().lower() == 'y'
    
    args = parser.parse_args()
    
    packages = list_packages(args.exclude_system, filter_system)
    if not packages:
        console.print("[red]No packages found on the device.[/red]")
        return

    table = Table(title="Installed Applications")
    table.add_column("Index", justify="center", style="cyan", no_wrap=True)
    table.add_column("Package", style="green", no_wrap=True)

    for i, package in enumerate(packages, 1):
        table.add_row(str(i), package)

    console.print(table)

    choice = console.input("[bold cyan]Enter the number of the APK you want to pull:[/] ").strip()

    try:
        selected_index = int(choice) - 1
        if selected_index < 0 or selected_index >= len(packages):
            raise ValueError
        selected_package = packages[selected_index]
    except ValueError:
        console.print("[red]❌ Invalid selection. Exiting.[/]")
        return

    apk_path = get_apk_path(selected_package)
    if apk_path:
        pull_apk(apk_path, selected_package)
    else:
        console.print(f"[red]⚠ Could not retrieve APK path for {selected_package}.[/]")

if __name__ == "__main__":
    main()