#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Script by L0WK3Y
# https://github.com/L0WK3Y-IAAN
# ---------------------------------------------------------------------------

"""
auto-frida-patch.py

1) Dynamically fetches the current Frida version from GitHub.
2) Automatically creates a keystore if not found.
3) Detects .apk files in both the root folder and the src/ folder. 
   Prompts user to pick one.
4) Injects Frida Gadget, rebuilds, and signs the APK.
5) Places all temp files (including the signed APK) into the output folder.
6) Optionally cleans up:
   - Frida .xz & .so
   - output/apk_working folder
   - output/app_patched.apk (unsigned)
   - output/signed_app_patched.apk.idsig
   - output/my-release-key.jks (the keystore itself!)

Leaving only: <original>.apk (in root/src) and output/signed_app_patched.apk
"""

import os
import sys
import subprocess
import shutil
import requests
import lzma

try:
    from colorama import init, Fore, Style
except ImportError:
    print("[-] colorama not installed. Please run: pip install colorama")
    sys.exit(1)

# Initialize colorama for Windows console compatibility
init(autoreset=True)

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# We fetch FRIDA_VERSION dynamically
FRIDA_VERSION = None  
FRIDA_BASE_URL_TEMPLATE = "https://github.com/frida/frida/releases/download/{version}"

# All build/sign artifacts go in this output folder
OUTPUT_FOLDER = "src/output"
# Working folder for apktool within the output directory
WORKING_FOLDER = os.path.join(OUTPUT_FOLDER, "apk_working")

# Keystore details (note: placed in output folder, removed if cleanup is chosen)
KEYSTORE_FILE = os.path.join(OUTPUT_FOLDER, "my-release-key.jks")
KEY_ALIAS = "mykeyalias"
KEYSTORE_PASS = "my_password"
KEYTOOL_DNAME = "CN=Test User, OU=Dev, O=MyCompany, L=MyCity, ST=MyState, C=US"

# Color shortcuts
INFO = Fore.MAGENTA + Style.NORMAL
SUCCESS = Fore.GREEN + Style.BRIGHT
WARNING = Fore.YELLOW + Style.BRIGHT
ERROR = Fore.RED + Style.NORMAL
RESET = Style.RESET_ALL

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def run_command(cmd):
    """Runs a shell command, exiting on error, with colorized logging."""
    print(f"{INFO}[run_command]{RESET} {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"{ERROR}[-] Command failed with exit code {e.returncode}:{RESET} {cmd}")
        sys.exit(e.returncode)

def get_latest_frida_version():
    """
    Fetches the latest Frida release version from GitHub.
    Returns a string like '16.6.8'.
    """
    url = "https://api.github.com/repos/frida/frida/releases/latest"
    print(f"{INFO}[*] Checking latest Frida version via GitHub API:{RESET} {url}")
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        tag = data.get("tag_name", "")
        if not tag:
            raise ValueError("No 'tag_name' in release data.")
        return tag.lstrip("v")  # remove leading 'v'
    except Exception as e:
        print(f"{ERROR}[-] Could not fetch latest Frida version: {e}{RESET}")
        sys.exit(1)

def ensure_keystore_exists():
    """
    Creates a keystore in OUTPUT_FOLDER if not found. 
    Warning: we also remove it if the user chooses cleanup later!
    """
    if os.path.exists(KEYSTORE_FILE):
        print(f"{SUCCESS}[+] Keystore already exists:{RESET} {KEYSTORE_FILE}")
        return

    print(f"{WARNING}[!] Keystore not found. Creating one with keytool...{RESET}")
    # Make sure the output folder exists
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    cmd_keytool = (
        f'keytool -genkeypair '
        f'-alias "{KEY_ALIAS}" '
        f'-keyalg RSA -keysize 2048 -validity 10000 '
        f'-dname "{KEYTOOL_DNAME}" '
        f'-storepass "{KEYSTORE_PASS}" '
        f'-keypass "{KEYSTORE_PASS}" '
        f'-keystore "{KEYSTORE_FILE}" '
        f'-v'
    )
    run_command(cmd_keytool)
    print(f"{SUCCESS}[+] Keystore created:{RESET} {KEYSTORE_FILE}")

def get_device_arch():
    """
    Uses adb to get the device's primary CPU architecture.
    """
    try:
        output = subprocess.check_output(["adb", "shell", "getprop", "ro.product.cpu.abi"])
        abi = output.decode().strip()
        if not abi:
            raise ValueError("Empty ABI from ADB.")
        return abi
    except subprocess.CalledProcessError as e:
        print(f"{ERROR}[-] Error calling adb: {e}{RESET}")
        sys.exit(1)
    except ValueError as e:
        print(f"{ERROR}[-] {e}{RESET}")
        sys.exit(1)

def map_frida_arch(android_abi):
    """
    Maps an Android ABI string to the Frida naming pattern.
    """
    mapping = {
        "armeabi-v7a": "android-arm",
        "arm64-v8a":   "android-arm64",
        "x86":         "android-x86",
        "x86_64":      "android-x86_64",
    }
    if android_abi not in mapping:
        print(f"{ERROR}[-] Unsupported or unknown ABI: {android_abi}{RESET}")
        sys.exit(1)
    return mapping[android_abi]

def download_file(url, dst):
    """
    Downloads a file from url to dst with requests, raising on error.
    """
    print(f"{INFO}[*] Downloading{RESET} {url} -> {dst}")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(dst, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except requests.RequestException as e:
        print(f"{ERROR}[-] Download failed: {e}{RESET}")
        sys.exit(1)
    print(f"{SUCCESS}[+] Download complete:{RESET} {dst}")

def decompress_xz(xz_file, out_file):
    """
    Decompresses an XZ file using Python's lzma, writing to out_file.
    """
    print(f"{INFO}[*] Decompressing{RESET} {xz_file} -> {out_file}")
    try:
        with lzma.open(xz_file, "rb") as f_in, open(out_file, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    except Exception as e:
        print(f"{ERROR}[-] Decompression error: {e}{RESET}")
        sys.exit(1)
    print(f"{SUCCESS}[+] Decompression complete:{RESET} {out_file}")

def find_apks_in_paths(paths):
    """
    Given a list of folder paths, returns a sorted list of APK files found in them.
    """
    found_apks = []
    for p in paths:
        if os.path.isdir(p):
            # list .apk in this directory
            for f_ in os.listdir(p):
                if f_.lower().endswith(".apk"):
                    full_path = os.path.join(p, f_)
                    found_apks.append(full_path)
    return sorted(found_apks)

def list_and_select_apk():
    """
    Looks for .apk in root (.) and 'src/' folder.
    Prompts user to pick one, returns the full path.
    """
    candidate_folders = [".", "src"]
    apks = find_apks_in_paths(candidate_folders)
    if not apks:
        print(f"{ERROR}[-] No .apk files found in root or src folder!{RESET}")
        sys.exit(1)

    print(f"{INFO}[*] APKs found in root/src:{RESET}")
    for i, apk_path in enumerate(apks, 1):
        print(f"   {i}. {apk_path}")

    while True:
        choice = input(f"{INFO}[?] Which APK to patch? Enter a number: {RESET}").strip()
        if choice.isdigit():
            c = int(choice)
            if 1 <= c <= len(apks):
                return apks[c - 1]
        print(f"{WARNING}[!] Invalid selection. Try again.{RESET}")

def prompt_cleanup(files_to_remove, folders_to_remove):
    """
    Asks if user wants to remove certain files and folders:
      - includes the working folder, .xz, .so, keystore, 
        the unsigned and signed .idsig, etc.
    """
    print()
    answer = input(f"{INFO}[?] Clean up temporary files/folders + key? (y/n): {RESET}").strip().lower()
    if answer not in ('y', 'yes'):
        print(f"{INFO}[*] Skipping cleanup. Everything remains in place.{RESET}")
        return

    # Remove the files
    for f in files_to_remove:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"{SUCCESS}[+] Removed file:{RESET} {f}")
            except OSError as e:
                print(f"{WARNING}[!] Failed to remove {f}: {e}{RESET}")

    # Remove the folders
    for folder in folders_to_remove:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f"{SUCCESS}[+] Removed folder:{RESET} {folder}")
            except OSError as e:
                print(f"{WARNING}[!] Failed to remove {folder}: {e}{RESET}")

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    # Check required tools
    for tool in ("adb", "apktool", "keytool"):
        if not shutil.which(tool):
            print(f"{ERROR}[-] Missing required tool '{tool}' in PATH.{RESET}")
            sys.exit(1)

    # Obtain latest Frida version
    global FRIDA_VERSION
    FRIDA_VERSION = get_latest_frida_version()
    frida_base_url = FRIDA_BASE_URL_TEMPLATE.format(version=FRIDA_VERSION)

    # Ensure the output folder exists
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Ensure keystore is ready
    ensure_keystore_exists()

    # Pick an APK from root or src
    selected_apk = list_and_select_apk()
    print(f"{SUCCESS}[+] Selected APK:{RESET} {selected_apk}")

    # Detect device ABI
    print(f"{INFO}[*] Detecting device ABI...{RESET}")
    device_abi = get_device_arch()
    print(f"{SUCCESS}[+] Device ABI:{RESET} {device_abi}")

    # Map to frida arch
    frida_arch = map_frida_arch(device_abi)
    print(f"{INFO}[*] Mapped device ABI to Frida arch:{RESET} {frida_arch}")

    # Prepare Frida download paths in the output folder
    frida_filename_xz = os.path.join(OUTPUT_FOLDER, f"frida-gadget-{FRIDA_VERSION}-{frida_arch}.so.xz")
    frida_filename_so = os.path.join(OUTPUT_FOLDER, f"frida-gadget-{FRIDA_VERSION}-{frida_arch}.so")
    frida_download_url = f"{frida_base_url}/{os.path.basename(frida_filename_xz)}"

    # We'll remove these if user chooses cleanup
    temp_files = [
        frida_filename_xz,          # downloaded .xz
        frida_filename_so,          # decompressed .so
        KEYSTORE_FILE,              # the keystore
        os.path.join(OUTPUT_FOLDER, "app_patched.apk"),         # intermediate unsigned APK
        os.path.join(OUTPUT_FOLDER, "signed_app_patched.apk.idsig")  # apksigner metadata
    ]
    temp_folders = [WORKING_FOLDER]

    # Remove old if exist
    for f_ in (frida_filename_xz, frida_filename_so):
        if os.path.exists(f_):
            os.remove(f_)

    # Download & decompress
    download_file(frida_download_url, frida_filename_xz)
    decompress_xz(frida_filename_xz, frida_filename_so)

    if not os.path.exists(frida_filename_so):
        print(f"{ERROR}[-] Decompressed .so file not found.{RESET}")
        sys.exit(1)

    # apktool decompile
    print(f"{INFO}[*] Checking/cleaning folder '{WORKING_FOLDER}'...{RESET}")
    if os.path.exists(WORKING_FOLDER):
        print(f"{WARNING}[!] Removing existing {WORKING_FOLDER}...{RESET}")
        shutil.rmtree(WORKING_FOLDER)
    os.makedirs(WORKING_FOLDER, exist_ok=True)

    run_command(f"apktool d -f \"{selected_apk}\" -o \"{WORKING_FOLDER}\"")

    # Copy frida so
    lib_folder = os.path.join(WORKING_FOLDER, "lib", device_abi)
    os.makedirs(lib_folder, exist_ok=True)
    gadget_dst = os.path.join(lib_folder, "libfrida-gadget.so")
    print(f"{INFO}[*] Copying Frida Gadget ->{RESET} {gadget_dst}")

    try:
        shutil.copy(frida_filename_so, gadget_dst)
    except OSError as e:
        print(f"{ERROR}[-] Failed copying .so: {e}{RESET}")
        sys.exit(1)

    # Rebuild -> app_patched.apk in output folder
    patched_apk = os.path.join(OUTPUT_FOLDER, "app_patched.apk")
    print(f"{INFO}[*] Building patched APK ->{RESET} {patched_apk}")
    run_command(f"apktool b \"{WORKING_FOLDER}\" -o \"{patched_apk}\"")

    # Sign -> signed_app_patched.apk in output folder
    signed_apk = os.path.join(OUTPUT_FOLDER, "signed_app_patched.apk")
    print(f"{INFO}[*] Signing the APK ->{RESET} {signed_apk}")

    apksigner_path = shutil.which("apksigner")
    if apksigner_path:
        print(f"{INFO}[*] Using apksigner...{RESET}")
        cmd_sign = (
            f"apksigner sign "
            f"--ks \"{KEYSTORE_FILE}\" "
            f"--ks-key-alias \"{KEY_ALIAS}\" "
            f"--ks-pass pass:{KEYSTORE_PASS} "
            f"--out \"{signed_apk}\" "
            f"\"{patched_apk}\""
        )
        run_command(cmd_sign)
        print(f"{SUCCESS}[+] Signed APK:{RESET} {signed_apk}")
    else:
        # fallback jarsigner
        jarsigner_path = shutil.which("jarsigner")
        if not jarsigner_path:
            print(f"{ERROR}[-] apksigner/jarsigner not found, cannot sign!{RESET}")
            sys.exit(1)

        print(f"{WARNING}[!] apksigner not found, using jarsigner...{RESET}")
        cmd_jarsigner = (
            f"jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 "
            f"-keystore \"{KEYSTORE_FILE}\" -storepass \"{KEYSTORE_PASS}\" "
            f"\"{patched_apk}\" \"{KEY_ALIAS}\""
        )
        run_command(cmd_jarsigner)

        # optional zipalign
        zipalign_path = shutil.which("zipalign")
        if zipalign_path:
            aligned_apk = os.path.join(OUTPUT_FOLDER, "aligned_app_patched.apk")
            print(f"{INFO}[*] zipaligning ->{RESET} {aligned_apk}")
            run_command(f"zipalign -v 4 \"{patched_apk}\" \"{aligned_apk}\"")
            print(f"{SUCCESS}[+] Signed & aligned:{RESET} {aligned_apk}")
        else:
            print(f"{WARNING}[!] zipalign not found; skipping alignment.{RESET}")
            print(f"{SUCCESS}[+] Signed (un-aligned) APK:{RESET} {patched_apk}")

    print(f"\n{SUCCESS}[*] Done!{RESET}")
    print("Install the signed APK with:")
    print(f"  {INFO}adb install -r \"{signed_apk}\"{RESET}\n")

    # Clean up prompt
    prompt_cleanup(temp_files, temp_folders)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"{ERROR}\n[-] Interrupted by user. Exiting...{RESET}")
        os.system('cls' if os.name == 'nt' else 'clear')
        sys.exit(1)
