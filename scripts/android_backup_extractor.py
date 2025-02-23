#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Script by L0WK3Y
# https://github.com/L0WK3Y-IAAN
# ---------------------------------------------------------------------------
import os
import sys
import struct
import tarfile
import zlib

try:
    from colorama import init, Fore, Style
except ImportError:
    print("[-] colorama not installed. Please run: pip install colorama")
    sys.exit(1)

# Initialize colorama for colored output
init(autoreset=True)

# Colors
INFO = Fore.MAGENTA + Style.NORMAL
SUCCESS = Fore.GREEN + Style.BRIGHT
WARNING = Fore.YELLOW + Style.BRIGHT
ERROR = Fore.RED + Style.BRIGHT
RESET = Style.RESET_ALL

# Output folder for extracted backups
OUTPUT_BASE = "src/output"

def is_android_backup(file_path):
    """Checks if a file is a valid Android backup."""
    with open(file_path, "rb") as f:
        header = f.read(15)
        return header.startswith(b"ANDROID BACKUP")

def convert_ab_to_tar(input_ab, output_tar):
    """Extracts the tar file from a .ab backup, decompressing if needed."""
    print(f"{INFO}[*] Converting {input_ab} to {output_tar}...{RESET}")

    with open(input_ab, "rb") as ab_file:
        header = ab_file.read(24)  # Read first 24 bytes
        magic, version, compressed = struct.unpack(">14sH?", header[:17])

        if magic != b"ANDROID BACKUP":
            print(f"{ERROR}[-] Error: Not a valid Android backup file!{RESET}")
            sys.exit(1)

        print(f"{INFO}[*] Backup version: {version}, Compression: {'Yes' if compressed else 'No'}{RESET}")

        with open(output_tar, "wb") as tar_file:
            if compressed:
                print(f"{INFO}[*] Decompressing backup...{RESET}")

                decompressor = zlib.decompressobj()
                while True:
                    chunk = ab_file.read(4096)
                    if not chunk:
                        break
                    tar_file.write(decompressor.decompress(chunk))
                tar_file.write(decompressor.flush())

            else:
                print(f"{INFO}[*] Backup is not compressed, extracting raw tar file.{RESET}")
                tar_file.write(ab_file.read())  # Write the remaining raw tar data

    print(f"{SUCCESS}[+] Converted {input_ab} -> {output_tar}{RESET}")

def extract_tar(tar_file, output_dir):
    """Extracts a tar archive."""
    print(f"{INFO}[*] Extracting {tar_file} to {output_dir}...{RESET}")

    os.makedirs(output_dir, exist_ok=True)

    with tarfile.open(tar_file, "r") as tar:
        tar.extractall(path=output_dir)

    print(f"{SUCCESS}[+] Extracted {tar_file} -> {output_dir}{RESET}")

def find_ab_files():
    """Searches for .ab files in the root and src/ directories."""
    search_paths = [".", "src"]
    ab_files = []

    for path in search_paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.lower().endswith(".ab"):
                    ab_files.append(os.path.join(path, file))

    return ab_files

def list_and_select_ab():
    """Lists all .ab files and lets the user select one."""
    ab_files = find_ab_files()

    if not ab_files:
        print(f"{ERROR}[-] No Android backup (.ab) files found in root or src folder!{RESET}")
        sys.exit(1)

    print(f"{INFO}[*] Found the following .ab backups:{RESET}")
    for i, ab_file in enumerate(ab_files, 1):
        print(f"{Fore.GREEN}[{i}] {ab_file}{RESET}")

    while True:
        choice = input(f"{INFO}[?] Select a file to extract (number): {RESET}").strip()
        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(ab_files):
                return ab_files[choice - 1]
        print(f"{WARNING}[!] Invalid selection. Try again.{RESET}")

def delete_file(file_path):
    """Safely deletes a file."""
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"{SUCCESS}[+] Deleted temporary file: {file_path}{RESET}")
        except Exception as e:
            print(f"{WARNING}[!] Failed to delete {file_path}: {e}{RESET}")

def main():
    print(f"{INFO}\n=== Android Backup Extractor ==={RESET}\n")

    # Select an AB file
    backup_ab = list_and_select_ab()
    backup_filename = os.path.basename(backup_ab).replace(".ab", "")

    # Define output locations
    tar_file = os.path.join(OUTPUT_BASE, f"{backup_filename}.tar")
    output_dir = os.path.join(OUTPUT_BASE, backup_filename)

    # Ensure output base exists
    os.makedirs(OUTPUT_BASE, exist_ok=True)

    print(f"{SUCCESS}[+] Selected Backup:{RESET} {backup_ab}")

    if not is_android_backup(backup_ab):
        print(f"{ERROR}[-] Error: Not a valid Android backup file!{RESET}")
        sys.exit(1)

    convert_ab_to_tar(backup_ab, tar_file)
    extract_tar(tar_file, output_dir)

    # Delete the .tar file after extraction
    delete_file(tar_file)

    print(f"\n{SUCCESS}[✓] All done! Extracted files are in:{RESET} {output_dir}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{ERROR}[-] User interrupted process. Exiting...{RESET}")
        sys.exit(1)
