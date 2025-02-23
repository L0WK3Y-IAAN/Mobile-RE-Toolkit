```
███╗   ███╗   ██████╗    ███████╗████████╗
████╗ ████║   ██╔══██╗   ██╔════╝╚══██╔══╝
██╔████╔██║   ██████╔╝   █████╗     ██║   
██║╚██╔╝██║   ██╔══██╗   ██╔══╝     ██║   
██║ ╚═╝ ██║██╗██║  ██║██╗███████╗██╗██║   
╚═╝     ╚═╝╚═╝╚═╝  ╚═╝╚═╝╚══════╝╚═╝╚═╝    
```


# Mobile RE Toolkit

[![License](https://img.shields.io/github/license/L0WK3Y-IAAN/Mobile-RE-Toolkit?color=blue)](LICENSE)
[![Issues](https://img.shields.io/github/issues/L0WK3Y-IAAN/Mobile-RE-Toolkit)](https://github.com/L0WK3Y-IAAN/Mobile-RE-Toolkit/issues)
[![Stars](https://img.shields.io/github/stars/L0WK3Y-IAAN/Mobile-RE-Toolkit)](https://github.com/L0WK3Y-IAAN/Mobile-RE-Toolkit/stargazers)
[![Forks](https://img.shields.io/github/forks/L0WK3Y-IAAN/Mobile-RE-Toolkit)](https://github.com/L0WK3Y-IAAN/Mobile-RE-Toolkit/network/members)

A **lightweight** but **powerful** toolkit for mobile reverse engineering, patching Android APKs with Frida Gadget, and more.  
*(Code name: “MOBILE-RE-TOOLKIT” or "MRT")*

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Examples](#examples)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Disclaimer](#disclaimer)

---

## Features

- **Frida Gadget Injection** – Dynamically download & inject Frida Gadget for various architectures.  
- **APK Tooling** – Decompile, rebuild, and sign Android APKs automatically.  
- **Scripted Workflows** – Convenient Python scripts for automating repetitive tasks.  
- **Cross-Platform** – Runs on Windows, macOS, and Linux.  
- **Cleanup** – Optionally remove all temp artifacts after patching.

---

## Installation

1. **Clone** this repo:
   ```bash
   git clone https://github.com/L0WK3Y-IAAN/Mobile-RE-Toolkit.git
   ```
2. **Install** the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Make sure you have:
   - [`adb`](https://developer.android.com/studio/command-line/adb)  
   - [`apktool`](https://ibotpeaches.github.io/Apktool/)  
   - A **Java Keytool** (part of the JDK)  
   - Optionally [`apksigner`](https://developer.android.com/studio/command-line/apksigner) or `jarsigner` in your PATH.

---

## Usage

1. **Select** the script you want to run from the **main menu** (`main.py`):
   ```bash
   python main.py
   ```
2. **Pick** an APK from the root folder or `src/`.  
3. **Wait** for the patching/signing process to complete.  
4. (Optional) **Clean Up** the working directories to keep things tidy.

---

## Examples

### Quick Patch Flow

```bash
python main.py
# => [Select "Auto Frida Patch" script]
# => [Pick your target .apk to patch]
# => Done! Final 'signed_app_patched.apk' in ./output
```

### Screenshot

*(Include a screenshot or terminal recording to showcase the process.)*

---

## Roadmap

- [ ] Support additional hooking frameworks  
- [ ] Add multi-DEX patching capabilities  
- [ ] Enhanced logging & error handling  
- [ ] Optional Docker container usage  

---

## Contributing

1. **Fork** the project  
2. **Create** your feature branch (`git checkout -b feature/super_cool_upgrade`)  
3. **Commit** your changes (`git commit -m 'Add super cool upgrade'`)  
4. **Push** to the branch (`git push origin feature/super_cool_upgrade`)  
5. **Open** a Pull Request

---

## License

Distributed under the **MIT License**.  
See [`LICENSE`](LICENSE) for more details.

---

## Disclaimer

> **This toolkit is intended for educational and testing purposes only.**  
> **Do not** use it on apps you do not have permission to modify.  
> The maintainers assume **no liability** for any misuse or damages caused.

---

**Enjoy hacking!** For suggestions, questions, or comments, feel free to open an [issue](https://github.com/L0WK3Y-IAAN/Mobile-RE-Toolkit/issues) or submit a pull request.
