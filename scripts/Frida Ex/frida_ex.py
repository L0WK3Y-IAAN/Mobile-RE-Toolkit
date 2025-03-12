#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# FridaEX Automation Tool (Enhanced)
# - Downloads/Installs Frida Server
# - Runs Interactive Frida Shell After Injection
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

FRIDA_SCRIPTS_FOLDER = "scripts/Frida Script Downloader/scripts"
FRIDA_RELEASES_URL = "https://api.github.com/repos/frida/frida/releases/latest"  # GitHub API endpoint
TEMP_DOWNLOAD_PATH = "frida-server.xz"
EXTRACTED_BIN_PATH = "frida-server"

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def run_as_root(device_id, *args):
    """
    Accepts multiple arguments and joins them into one shell command.
    Example usage:
        run_as_root(device_id, "pidof", "frida-server")
        run_as_root(device_id, "chmod", "755", "/data/local/tmp/frida-server")
    """
    # Join all args into a single string
    command_str = " ".join(args)
    cmd = ["adb", "-s", device_id, "shell", "su", "-c", command_str]
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def is_device_rooted(device_id):
    """
    Checks if 'su -c "whoami"' returns 'root'. If so, we consider the device rooted.
    """
    console.print("[cyan]🔍 Checking if 'su' works on this device...[/]")
    result = run_as_root(device_id, "whoami")
    if result and "root" in result.stdout.strip().lower():
        console.print("[green]✅ Device can run commands as root (su is working).[/]")
        return True
    console.print("[yellow]⚠ Device is not rooted or 'su' not granted. Proceeding in user mode...[/]")
    return False


def get_frida_devices():
    """Detects connected Frida devices (USB or remote)."""
    try:
        return frida.enumerate_devices()
    except Exception as e:
        console.print(f"[red]❌ Error getting devices: {e}[/]")
        return []

def select_device(devices):
    """Prompts the user to select a Frida device."""
    if not devices:
        console.print("[red]❌ No devices found! Make sure a device is connected.[/]")
        sys.exit(1)

    console.print("\n[cyan]📱 Available Devices:[/]")
    table = Table(title="Connected Devices", show_header=True, header_style="bold magenta")
    table.add_column("Index", justify="center", style="cyan", no_wrap=True)
    table.add_column("Device ID", style="green")
    table.add_column("Type", style="yellow")

    for i, dev in enumerate(devices, 1):
        dev_type = dev.type.capitalize()  # e.g. "Usb", "Remote", "Socket"
        table.add_row(str(i), dev.id, dev_type)
    console.print(table)

    while True:
        choice = Prompt.ask("[bold cyan]Enter the number of the device to use[/]").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(devices):
            return devices[int(choice) - 1]
        console.print("[bold red]⚠ Invalid selection. Try again.[/]")

def detect_device_arch(device_id):
    """
    Detects the device architecture by reading 'ro.product.cpu.abi'.
    Returns one of: 'arm', 'arm64', 'x86', 'x86_64' (if recognized).
    """
    console.print("[cyan]🔍 Detecting device architecture...[/]")
    cmd = ["adb", "-s", device_id, "shell", "getprop", "ro.product.cpu.abi"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    abi = result.stdout.strip().lower()

    # Map typical ABI strings to frida's naming
    if "arm64" in abi:
        arch = "arm64"
    elif "arm" in abi:
        arch = "arm"
    elif "x86_64" in abi:
        arch = "x86_64"
    elif "x86" in abi:
        arch = "x86"
    else:
        console.print(f"[red]❌ Unrecognized ABI: {abi}. Defaulting to arm.[/]")
        arch = "arm"

    console.print(f"[green]✅ Detected architecture: {arch}[/]")
    return arch

def download_frida_server_for_arch(arch):
    """
    Downloads the latest Frida server for the given architecture (arm, arm64, x86, x86_64)
    from GitHub Releases, and saves it to TEMP_DOWNLOAD_PATH (xz-compressed).
    """
    console.print("[cyan]🔍 Fetching latest Frida release from GitHub...[/]")
    r = requests.get(FRIDA_RELEASES_URL, timeout=15)
    if r.status_code != 200:
        console.print(f"[red]❌ Failed to query GitHub API: {r.status_code}[/]")
        sys.exit(1)

    data = r.json()
    assets = data.get("assets", [])
    if not assets:
        console.print("[red]❌ No assets found in the latest release![/]")
        sys.exit(1)

    # The Frida server file name typically looks like: frida-server-<version>-android-<arch>.xz
    # We'll look for something ending with "android-{arch}.xz"
    desired_suffix = f"android-{arch}.xz"
    download_url = None
    for asset in assets:
        name = asset["name"].lower()
        # Must contain 'frida-server' AND end with 'android-ARCH.xz'
        if "frida-server" in name and name.endswith(desired_suffix):
            download_url = asset["browser_download_url"]
            break


    if not download_url:
        console.print(f"[red]❌ Could not find a frida-server asset for: {desired_suffix}[/]")
        sys.exit(1)

    console.print(f"[cyan]🔽 Downloading: {download_url}[/]")
    with requests.get(download_url, stream=True, timeout=30) as resp:
        resp.raise_for_status()
        with open(TEMP_DOWNLOAD_PATH, "wb") as f:
            shutil.copyfileobj(resp.raw, f)

    console.print("[green]✅ Download complete.[/]")

def extract_frida_server():
    """
    Extracts the XZ-compressed file in TEMP_DOWNLOAD_PATH into EXTRACTED_BIN_PATH.
    """
    console.print("[cyan]🔍 Extracting frida-server from XZ...[/]")
    with lzma.open(TEMP_DOWNLOAD_PATH, "rb") as xz_file:
        with open(EXTRACTED_BIN_PATH, "wb") as out_file:
            shutil.copyfileobj(xz_file, out_file)
    console.print("[green]✅ Extraction complete.[/]")

def push_frida_server_to_device(device_id):
    """
    Pushes the extracted frida-server binary to /data/local/tmp/frida-server,
    then makes it executable.
    """
    console.print("[cyan]📂 Pushing frida-server to /data/local/tmp/...[/]")
    subprocess.run(["adb", "-s", device_id, "push", EXTRACTED_BIN_PATH, "/data/local/tmp/frida-server"],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    console.print("[cyan]🔑 Setting frida-server as executable...[/]")
    run_as_root(device_id, "chmod 755 /data/local/tmp/frida-server")

def download_and_install_frida_server(device_id):
    """
    If /data/local/tmp/frida-server is not present, download the correct architecture
    from GitHub, extract, push, and clean up.
    """
    console.print("[cyan]🔍 Checking if frida-server is already on device...[/]")
    ls_result = subprocess.run(["adb", "-s", device_id, "shell", "ls", "/data/local/tmp/frida-server"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if "frida-server" in ls_result.stdout.strip():
        console.print("[yellow]⚠ frida-server already exists. Skipping download.[/]")
        return

    # Otherwise, we download
    arch = detect_device_arch(device_id)
    download_frida_server_for_arch(arch)
    extract_frida_server()
    push_frida_server_to_device(device_id)

    # Clean up local files
    if os.path.exists(TEMP_DOWNLOAD_PATH):
        os.remove(TEMP_DOWNLOAD_PATH)
    if os.path.exists(EXTRACTED_BIN_PATH):
        os.remove(EXTRACTED_BIN_PATH)

def is_frida_running(device_id):
    console.print("[cyan]🔍 Checking if Frida server is running...[/]")
    
    # Use a more reliable check method
    result = run_as_root(device_id, 'sh -c "ps -A | grep frida-server"')
    
    if result.stdout.strip():
        console.print(f"[green]✅ Frida server is running: {result.stdout.strip()}[/]")
        return True
    console.print("[red]❌ Frida server is NOT running.[/]")
    return False


def start_frida_server(device_id):
    """
    Starts frida-server in the background via 'su -c'.
    """
    console.print("[cyan]🚀 Attempting to start frida-server...[/]")
    run_as_root(device_id, "chmod +x /data/local/tmp/frida-server")
    run_as_root(device_id, "nohup /data/local/tmp/frida-server > /dev/null 2>&1 &")

    time.sleep(3)
    return is_frida_running(device_id)

def ensure_frida_server(device_id):
    """
    Ensures frida-server is present and running on the device.
    If not present, downloads/installs it. If not running, starts it.
    """
    if is_frida_running(device_id):
        return
    # If not installed, download + install
    download_and_install_frida_server(device_id)
    if not start_frida_server(device_id):
        console.print("[red]❌ Unable to start Frida server![/]")
        sys.exit(1)

def list_installed_packages(device_id):
    """
    Retrieves a list of installed packages from the device.
    Optionally hides system packages by using 'pm list packages -3'.
    """
    console.print("[cyan]🔍 Retrieving installed packages...[/]")

    # Ask if the user wants to hide system packages
    hide_system = Prompt.ask("[bold cyan]Hide system packages?[/] (y/N)", default="N").strip().lower()

    if hide_system.startswith("y"):
        # -3 => list only third-party packages
        pm_command = ["adb", "-s", device_id, "shell", "pm", "list", "packages", "-3"]
        console.print("[green]Hiding system packages (only showing user-installed apps).[/]")
    else:
        # Shows all packages (system + user)
        pm_command = ["adb", "-s", device_id, "shell", "pm", "list", "packages"]

    result = subprocess.run(pm_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    lines = result.stdout.strip().splitlines()

    # Clean up output by removing 'package:' prefix
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

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    console.print("\n[bold magenta]🔎 FridaEX Automation Tool 🔍[/]\n")

    # 1. Pick a device from frida.enumerate_devices()
    devices = get_frida_devices()
    device = select_device(devices)
    device_id = device.id

    # 2. Check if 'su' is actually available
    rooted = is_device_rooted(device_id)
    # If not rooted, you can decide to continue or to exit:
    # if not rooted:
    #     sys.exit("[red]This script requires root but device is not rooted. Exiting.[/]")

    # 3. Ensure frida-server is installed & running
    ensure_frida_server(device_id)

    # 4. List installed packages and select one
    packages = list_installed_packages(device_id)
    chosen_package = select_package(packages)

    # 5. Select a local Frida script
    script_path = select_frida_script()
    if not script_path:
        sys.exit(1)

    # 6. Launch Frida interactive shell
    console.print("[cyan]🚀 Launching Frida shell...[/]")
    frida_cmd = ["frida", "-U", "-f", chosen_package, "-l", script_path]
    subprocess.run(frida_cmd)

if __name__ == "__main__":
    main()
