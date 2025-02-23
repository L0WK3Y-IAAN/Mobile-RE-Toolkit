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
✅ Stores output in `src/output/{APK_NAME}_EXTRACTION`
"""

import os
import re
import argparse
import csv
import subprocess
import shutil
import sys

# Auto-detect apktool
APKTOOL_PATH = shutil.which("apktool")

if not APKTOOL_PATH:
    print("❌ apktool is not installed or not in PATH! Please install it and try again.")
    sys.exit(1)

print(f"✅ Using apktool at: {APKTOOL_PATH}")

# Default output directory
OUTPUT_BASE_DIR = "src/output"

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
        print("❌ No APKs found in the root or `src/` directories!")
        sys.exit(1)

    print("\n📦 Available APKs:")
    for i, apk in enumerate(apks, start=1):
        print(f"  [{i}] {apk}")

    while True:
        choice = input("\n🔹 Select an APK by number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(apks):
            return apks[int(choice) - 1]
        print("⚠ Invalid selection. Please enter a valid number.")

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
        print(f"⚠ Error processing file {file_path}: {e}")
    
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
        print(f"📂 Removing existing directory: {output_dir}")
        shutil.rmtree(output_dir)

    print(f"🔍 Decompiling APK: {apk_path} -> {output_dir}")

    try:
        subprocess.run([APKTOOL_PATH, "d", "-f", apk_path, "-o", output_dir], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error decompiling APK: {e}")
        return None

    return output_dir

def process_directory(directory, min_length):
    """
    Recursively extracts strings from files in a directory.

    Args:
        directory (str): Directory to scan.
        min_length (int): Minimum length of string to extract.

    Returns:
        list: Extracted strings.
    """
    unique_results = set()

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            extracted = extract_strings_from_file(file_path, min_length=min_length)
            unique_results.update(extracted)
    
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
        print(f"❌ Error: {input_path} does not exist.")
        return

    # If input is an APK, decompile it
    if input_path.endswith(".apk"):
        output_dir = decompile_apk(input_path)
        if not output_dir:
            print("❌ APK decompilation failed. Exiting...")
            return
    else:
        output_dir = input_path

    # Extract strings
    print(f"📑 Extracting strings from: {output_dir}")
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

        print(f"\n✅ Extracted strings saved to: {output_file}")
    except Exception as e:
        print(f"❌ Error writing to output file: {e}")

if __name__ == "__main__":
    main()
