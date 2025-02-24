#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# FridaEX Automation Tool (Enhanced) - Runs Interactive Frida Shell After Injection
# ---------------------------------------------------------------------------

import frida
import lzma
import os
import sys
import subprocess
import time
import requests
import shutil
import re
import shlex
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

console = Console()

FRIDA_SCRIPTS_FOLDER = "scripts/Frida Ex Wip/frida scripts"
FRIDA_RELEASES_URL = "https://github.com/frida/frida/releases/latest"
TEMP_DOWNLOAD_PATH = "frida-server.xz"
EXTRACTED_BIN_PATH = "frida-server"

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def get_connected_devices():
    """Detects connected Frida devices."""
    try:
        devices = frida.enumerate_devices()
        return devices
    except Exception as e:
        console.print(f"[red]❌ Error getting devices: {e}[/]")
        return []

def select_device(devices):
    """Prompts the user to select a device."""
    if not devices:
        console.print("[red]❌ No devices found! Make sure a device is connected and Frida server is running.[/]")
        sys.exit(1)

    console.print("\n[cyan]📱 Available Devices:[/]")

    table = Table(title="Connected Devices", show_header=True, header_style="bold magenta")
    table.add_column("Index", justify="center", style="cyan", no_wrap=True)
    table.add_column("Device ID", style="green")
    table.add_column("Type", style="yellow")

    for i, device in enumerate(devices, 1):
        device_type = "USB" if device.type == "usb" else "Remote"
        table.add_row(str(i), device.id, device_type)

    console.print(table)

    while True:
        choice = Prompt.ask("[bold cyan]Enter the number of the device to use[/]").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(devices):
            return devices[int(choice) - 1]
        console.print("[bold red]⚠ Invalid selection. Try again.[/]")

def is_frida_running(device_id):
    """Checks if Frida server is running."""
    console.print("[cyan]🔍 Checking if Frida server is running...[/]")

    result = subprocess.run(["adb", "-s", device_id, "shell", "pidof", "frida-server"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.stdout.strip():
        console.print("[green]✅ Frida server is already running.[/]")
        return True
    
    console.print("[red]❌ Frida server is NOT running.[/]")
    return False

def start_frida_server(device_id):
    """Attempts to start the Frida server if found on the device."""
    console.print("[cyan]🔍 Checking if Frida server exists in /data/local/tmp...[/]")

    result = subprocess.run(
        ["adb", "-s", device_id, "shell", "ls", "/data/local/tmp/frida-server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if "frida-server" in result.stdout.strip():
        console.print("[yellow]⚠ Frida server found. Attempting to start it...[/]")
        subprocess.run(["adb", "-s", device_id, "shell", "nohup", "/data/local/tmp/frida-server", "&"])
        time.sleep(3)

        if is_frida_running(device_id):
            return True

    console.print("[red]❌ Frida server failed to start![/]")
    return False

def ensure_frida_server(device_id):
    """Ensures Frida server is running, installs it if necessary."""
    if is_frida_running(device_id):
        return True
    if start_frida_server(device_id):
        return True
    console.print("[red]❌ Unable to start Frida server![/]")
    sys.exit(1)

def list_installed_packages():
    """Retrieves a list of installed packages from the device."""
    console.print("[cyan]🔍 Retrieving installed packages...[/]")

    result = subprocess.run("adb shell pm list packages",
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True)

    lines = result.stdout.strip().splitlines()
    packages = [line.replace("package:", "").strip() for line in lines if line.startswith("package:")]
    return packages

def select_package(packages):
    """Prompts the user to select a package from the list."""
    if not packages:
        console.print("[red]❌ No packages found on the device.[/]")
        sys.exit(1)

    table = Table(title="Installed Packages", show_header=True, header_style="bold magenta")
    table.add_column("Index", justify="center", style="cyan", no_wrap=True)
    table.add_column("Package Name", style="green")

    for i, pkg in enumerate(packages, 1):
        table.add_row(str(i), pkg)

    console.print(table)

    while True:
        choice = Prompt.ask("[bold cyan]Enter the number of the package to use[/]").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(packages):
            return packages[int(choice) - 1]
        console.print("[bold red]⚠ Invalid selection. Try again.[/]")

def select_frida_script():
    """Lists all .js scripts in FRIDA_SCRIPTS_FOLDER and prompts user to select one."""
    if not os.path.isdir(FRIDA_SCRIPTS_FOLDER):
        console.print(f"[red]❌ Scripts folder not found: {FRIDA_SCRIPTS_FOLDER}[/]")
        return None

    scripts = [f for f in os.listdir(FRIDA_SCRIPTS_FOLDER) if f.endswith(".js")]
    if not scripts:
        console.print("[red]❌ No .js scripts found in the folder.[/]")
        return None

    table = Table(title="Available Frida Scripts", show_header=True, header_style="bold magenta")
    table.add_column("Index", justify="center", style="cyan", no_wrap=True)
    table.add_column("Script Name", style="green")

    for i, script_name in enumerate(scripts, 1):
        table.add_row(str(i), script_name)

    console.print(table)

    while True:
        choice = Prompt.ask("[bold cyan]Enter the number of the script to use[/]").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(scripts):
            return os.path.join(FRIDA_SCRIPTS_FOLDER, scripts[int(choice) - 1])
        console.print("[bold red]⚠ Invalid selection. Try again.[/]")

def launch_frida_shell(device_id, package_name, script_path):
    """
    Ensures the package is running and launches the Frida shell.
    """

    console.print(f"\n[cyan]🚀 Ensuring {package_name} is running before injection...[/]")

    # Get the list of processes from Frida
    frida_processes = subprocess.run(["frida-ps", "-U"], stdout=subprocess.PIPE, text=True).stdout

    # Check if the process exists
    process_found = any(package_name in line for line in frida_processes.splitlines())

    if not process_found:
        console.print("[yellow]⚠ App is NOT detected by Frida. Trying to spawn...[/]")

        # Spawn the app and inject the script
        spawn_cmd = ["frida", "-U", "-f", package_name, "-l", script_path]
        subprocess.run(spawn_cmd)
        console.print("[green]✅ App spawned & Frida script injected successfully![/]")

    else:
        console.print("[green]✅ App is already running. Attaching Frida...[/]")

        # Attach to the running process instead of spawning
        attach_cmd = ["frida", "-U", "-n", package_name, "-l", script_path]
        subprocess.run(attach_cmd)

    console.print("[green]🎉 Injection complete. The app is now running with Frida![/]")



# ---------------------------------------------------------------------------
# Main Function
# ---------------------------------------------------------------------------

def main():
    console.print("\n[bold magenta]🔎 FridaEX Automation Tool 🔍[/]\n")

    # 1. Get and select the Frida device
    devices = get_connected_devices()
    device = select_device(devices)
    device_id = device.id

    # 2. Ensure Frida server is running
    ensure_frida_server(device_id)

    # 3. List installed packages and select one
    packages = list_installed_packages()
    chosen_package = select_package(packages)

    # 4. Select a Frida script
    script_path = select_frida_script()
    if not script_path:
        sys.exit(1)

    # 5. Launch Frida interactive shell
    launch_frida_shell(device_id, chosen_package, script_path)

if __name__ == "__main__":
    main()
