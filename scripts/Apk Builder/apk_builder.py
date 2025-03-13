#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Android APK Builder - Recompiles decompiled APK source code into APK & Signs It,
# with an option to clean up leftover artifacts at the end.
# ---------------------------------------------------------------------------

import os
import sys
import subprocess
import shutil
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

console = Console()
OUTPUT_DIR = "src/output"
APKTOOL_PATH = shutil.which("apktool")
APKSIGNER_PATH = shutil.which("apksigner")
ADB_PATH = shutil.which("adb")   # Check for adb

if not APKTOOL_PATH:
    console.print("[red]❌ Error: apktool is not found in the system environment variables![/]")
    console.print("[yellow]🔍 Ensure apktool is installed and added to PATH.[/]")
    sys.exit(1)

if not APKSIGNER_PATH:
    console.print("[red]❌ Error: apksigner is not found in the system environment variables![/]")
    console.print("[yellow]🔍 Ensure apksigner from Android SDK is installed and added to PATH.[/]")
    sys.exit(1)

if not ADB_PATH:
    console.print("[red]❌ Error: adb is not found in the system environment variables![/]")
    console.print("[yellow]🔍 Ensure adb is installed and added to PATH.[/]")
    sys.exit(1)

KEYSTORE_PATH = "debug.keystore"  # Default keystore
STORE_PASS = "android"
KEY_PASS = "android"
KEY_ALIAS = "androiddebugkey"

# Provide a full DName so keytool doesn't become interactive
DNAME = "CN=Android Debug,O=Android,C=US"

# ---------------------------------------------------------------------------
# Ensures we have a debug.keystore
# ---------------------------------------------------------------------------
def ensure_keystore():
    if os.path.exists(KEYSTORE_PATH):
        return  # Already exists

    console.print("[yellow]⚠ Keystore not found! Generating a new one...[/]")
    try:
        # Provide all necessary fields so keytool won't prompt
        key_cmd = [
            "keytool", "-genkey", "-v",
            "-keystore", KEYSTORE_PATH,
            "-storepass", STORE_PASS,
            "-alias", KEY_ALIAS,
            "-keypass", KEY_PASS,
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", "10000",
            "-dname", DNAME
        ]
        subprocess.run(key_cmd, check=True)
        console.print("[green]✅ Keystore created successfully![/]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Failed to create keystore! Error code {e.returncode}[/]")
        sys.exit(e.returncode)

# ---------------------------------------------------------------------------
# Finds valid Android "projects" in src/output
# ---------------------------------------------------------------------------
def find_android_projects():
    valid_projects = []

    if not os.path.exists(OUTPUT_DIR):
        console.print(f"[red]❌ Output directory '{OUTPUT_DIR}' does not exist.[/]")
        return []

    for folder in os.listdir(OUTPUT_DIR):
        folder_path = os.path.join(OUTPUT_DIR, folder)

        if not os.path.isdir(folder_path):
            continue

        manifest_path = os.path.join(folder_path, "AndroidManifest.xml")
        smali_folder = os.path.join(folder_path, "smali")
        dex_file = os.path.join(folder_path, "classes.dex")

        if os.path.exists(manifest_path) and (os.path.exists(smali_folder) or os.path.exists(dex_file)):
            valid_projects.append(folder_path)

    return valid_projects

# ---------------------------------------------------------------------------
# Let user pick one of the valid projects
# ---------------------------------------------------------------------------
def select_project(projects):
    console.print("\n[bold magenta]📦 Available Android Projects[/]\n")

    table = Table(title="Detected Projects", show_header=True, header_style="bold magenta")
    table.add_column("Index", justify="center", style="cyan", no_wrap=True)
    table.add_column("Project Folder", style="green")

    for i, project in enumerate(projects, 1):
        table.add_row(str(i), os.path.basename(project))

    console.print(table)

    while True:
        choice = Prompt.ask("[bold cyan]Enter the number of the project to build[/]").strip()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(projects):
                return projects[idx - 1]
        console.print("[red]⚠ Invalid selection. Try again.[/]")

# ---------------------------------------------------------------------------
# Build the APK with apktool
# ---------------------------------------------------------------------------
def build_apk(project_path):
    project_name = os.path.basename(project_path)
    console.print(f"\n[cyan]🚀 Building APK for {project_name}...[/]")

    build_output = os.path.join(OUTPUT_DIR, "build_output")
    os.makedirs(build_output, exist_ok=True)

    unsigned_apk = os.path.join(build_output, f"{project_name}_unsigned.apk")
    signed_apk = os.path.join(build_output, f"{project_name}_signed.apk")

    # Run apktool
    try:
        subprocess.run([
            APKTOOL_PATH, "b", project_path,
            "-o", unsigned_apk
        ], check=True)
        console.print(f"[green]✅ APK successfully built: {unsigned_apk}[/]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ APK build failed with code {e.returncode}![/]")
        sys.exit(e.returncode)

    # Sign the resulting APK
    sign_apk(unsigned_apk, signed_apk)

    # Prompt for cleanup
    prompt_cleanup(unsigned_apk, signed_apk)

    # Prompt for installation
    prompt_install(signed_apk)

# ---------------------------------------------------------------------------
# Sign the APK with apksigner
# ---------------------------------------------------------------------------
def sign_apk(unsigned_apk, signed_apk):
    console.print(f"[cyan]🔏 Signing APK...[/]")

    # Make sure keystore is available
    ensure_keystore()

    try:
        subprocess.run([
            APKSIGNER_PATH, "sign",
            "--ks", KEYSTORE_PATH,
            "--ks-pass", f"pass:{STORE_PASS}",
            "--key-pass", f"pass:{KEY_PASS}",
            "--ks-key-alias", KEY_ALIAS,
            "--out", signed_apk,
            unsigned_apk
        ], check=True)
        console.print(f"[green]✅ APK successfully signed: {signed_apk}[/]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ APK signing failed with code {e.returncode}![/]")
        sys.exit(e.returncode)

# ---------------------------------------------------------------------------
# Optionally remove leftover files: the unsigned APK and .idsig
# ---------------------------------------------------------------------------
def prompt_cleanup(unsigned_apk, signed_apk):
    # The .idsig file is automatically generated by apksigner
    idsig_file = signed_apk + ".idsig"

    ans = Prompt.ask(
        "[bold yellow]Would you like to remove leftover files (unsigned APK & .idsig)? (y/n)[/]",
        default="n"
    ).strip().lower()

    if ans.startswith("y"):
        # Remove the unsigned APK
        if os.path.exists(unsigned_apk):
            try:
                os.remove(unsigned_apk)
                console.print(f"[green]Removed leftover file:[/] {unsigned_apk}")
            except Exception as e:
                console.print(f"[red]Could not remove {unsigned_apk}: {e}[/]")

        # Remove the .idsig
        if os.path.exists(idsig_file):
            try:
                os.remove(idsig_file)
                console.print(f"[green]Removed leftover file:[/] {idsig_file}")
            except Exception as e:
                console.print(f"[red]Could not remove {idsig_file}: {e}[/]")
        console.print("[green]Cleanup complete![/]")
    else:
        console.print("[yellow]Skipping cleanup. All files remain in place.[/]")

# ---------------------------------------------------------------------------
# List connected devices using adb
# ---------------------------------------------------------------------------
def list_devices():
    try:
        result = subprocess.run([ADB_PATH, "devices"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Failed to run adb devices: {e}[/]")
        return []

    lines = result.stdout.strip().splitlines()
    devices = []
    for line in lines[1:]:  # Skip the header line
        line = line.strip()
        if line:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])
    return devices

# ---------------------------------------------------------------------------
# Prompt user to install the APK on a selected device
# ---------------------------------------------------------------------------
def prompt_install(signed_apk):
    ans = Prompt.ask(
        "[bold yellow]Would you like to install the signed APK on a connected device? (y/n)[/]",
        default="n"
    ).strip().lower()

    if not ans.startswith("y"):
        console.print("[yellow]Skipping APK installation.[/]")
        return

    devices = list_devices()
    if not devices:
        console.print("[red]❌ No connected devices found. Please connect a device and try again.[/]")
        return

    console.print("\n[bold magenta]📱 Connected Devices[/]\n")
    table = Table(title="Available Devices", show_header=True, header_style="bold magenta")
    table.add_column("Index", justify="center", style="cyan", no_wrap=True)
    table.add_column("Device ID", style="green")

    for i, device in enumerate(devices, 1):
        table.add_row(str(i), device)

    console.print(table)

    while True:
        choice = Prompt.ask("[bold cyan]Enter the number of the device to install the APK[/]").strip()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(devices):
                selected_device = devices[idx - 1]
                break
        console.print("[red]⚠ Invalid selection. Try again.[/]")

    console.print(f"[cyan]Installing APK on device {selected_device}...[/]")
    try:
        subprocess.run([ADB_PATH, "-s", selected_device, "install", "-r", signed_apk], check=True)
        console.print("[green]✅ APK installed successfully![/]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ APK installation failed with code {e.returncode}![/]")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    console.print("\n[bold magenta]🛠 Android APK Builder[/]\n")

    projects = find_android_projects()
    if not projects:
        console.print("[red]❌ No valid Android projects found in src/output![/]")
        return

    selected_project = select_project(projects)
    build_apk(selected_project)

if __name__ == "__main__":
    main()
