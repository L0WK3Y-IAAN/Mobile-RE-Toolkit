![](https://i.imgur.com/6ZPXXda.png)

# Mobile RE Toolkit  

[![License](https://img.shields.io/github/license/L0WK3Y-IAAN/Mobile-RE-Toolkit?color=blue)](LICENSE)
[![Issues](https://img.shields.io/github/issues/L0WK3Y-IAAN/Mobile-RE-Toolkit)](https://github.com/L0WK3Y-IAAN/Mobile-RE-Toolkit/issues)
[![Stars](https://img.shields.io/github/stars/L0WK3Y-IAAN/Mobile-RE-Toolkit)](https://github.com/L0WK3Y-IAAN/Mobile-RE-Toolkit/stargazers)
[![Forks](https://img.shields.io/github/forks/L0WK3Y-IAAN/Mobile-RE-Toolkit)](https://github.com/L0WK3Y-IAAN/Mobile-RE-Toolkit/network/members)  

A **lightweight** yet **powerful** toolkit designed for **Android Reverse Engineering**, **Frida Gadget Injection**, and **APK Patching**.  
*(Code name: “Mobile Reverse Engineering Toolkit” or **MRET**) 🔥*  

---

## 📖 Table of Contents  

- [Mobile RE Toolkit](#mobile-re-toolkit)
  - [📖 Table of Contents](#-table-of-contents)
  - [🚀 Features](#-features)
  - [🛠 Installation](#-installation)
  - [📜 Scripts](#-scripts)
    - [🔹 **Main Menu**](#-main-menu)
    - [🔹 **Frida Gadget Injector**](#-frida-gadget-injector)
    - [🔹 **Android Backup Extractor**](#-android-backup-extractor)
    - [🔹 **String Extractor**](#-string-extractor)
    - [🔹 **Malicious Indicator Detection**](#-malicious-indicator-detection)
  - [💡 Usage](#-usage)
  - [⚡ Examples](#-examples)
    - [**1️⃣ Quick Frida Injection Flow**](#1️⃣-quick-frida-injection-flow)
    - [**2️⃣ Extract Strings from an APK**](#2️⃣-extract-strings-from-an-apk)
    - [**3️⃣ Detect Malware Indicators in an APK**](#3️⃣-detect-malware-indicators-in-an-apk)
  - [🚧 Roadmap](#-roadmap)
  - [🤝 Contributing](#-contributing)
  - [📜 License](#-license)
  - [⚠ Disclaimer](#-disclaimer)
    - [🚀 **Happy Hacking!** 🔥](#-happy-hacking-)

---

## 🚀 Features  

✅ **APK Tooling** – Decompile, rebuild, and sign Android APKs automatically.  
✅ **Scripted Workflows** – Python-powered automation for repetitive tasks.  
✅ **Frida Integration** – Injects Frida Gadget into an APK and signs it.  
✅ **Backup Analysis** – Extracts and analyzes Android `.ab` backups.  
✅ **String Extraction** – Extracts readable strings from APKs for static analysis.  
✅ **Malware Detection** – Identifies suspicious indicators in extracted APK strings.  
✅ **Cross-Platform** – Works on **Windows, macOS, and Linux**.  
✅ **Cleanup Options** – Easily remove temp artifacts after processing.  

---

## 🛠 Installation  

1️⃣ **Clone** the repository:  
   ```bash
   git clone https://github.com/L0WK3Y-IAAN/Mobile-RE-Toolkit.git
   cd Mobile-RE-Toolkit
   ```  

2️⃣ **Install dependencies**:  
   ```bash
   pip install -r requirements.txt
   ```  

3️⃣ Ensure required tools are installed and accessible in your **PATH**:  
   - [`adb`](https://developer.android.com/studio/command-line/adb)  
   - [`apktool`](https://ibotpeaches.github.io/Apktool/)  
   - Java **Keytool** (part of the JDK)  
   - [`apksigner`](https://developer.android.com/studio/command-line/apksigner) or `jarsigner` (optional)  

---

## 📜 Scripts  

### 🔹 **Main Menu**  
- A **centralized dashboard** to browse and execute all scripts with an **interactive UI** powered by `rich`.  

### 🔹 **Frida Gadget Injector**  
- Automatically downloads the **latest Frida Gadget** from GitHub.  
- Injects it into an APK, signs it, and prepares it for deployment.  
- Supports **multiple architectures** (`arm64-v8a`, `armeabi-v7a`, `x86`, `x86_64`).  

### 🔹 **Android Backup Extractor**  
- Converts **Android `.ab` backups** to `.tar`.  
- Extracts contents for **further analysis** of saved app data.  

### 🔹 **String Extractor**  
- Uses `apktool` to **decompile APKs**.  
- Recursively extracts **readable strings** from all files.  
- Saves results in **CSV format** for analysis.  

### 🔹 **Malicious Indicator Detection**  
- Scans extracted APK strings for:  
  - 🔗 **C2 URLs & IPs**  
  - 📄 **Suspicious permissions**  
  - 🔑 **Encryption methods** (AES, XOR, RC4)  
  - 📡 **Dynamic code loading**  
  - 🏴 **Root detection & anti-debugging**  
  - 🎭 **Obfuscation techniques**  
  - ⚠ **High-entropy (Base64, encoded payloads)**  
- Generates a **detailed report** (`potential_indicators.csv`).  

---

## 💡 Usage  

1️⃣ **Run the toolkit menu**:  
   ```bash
   python main.py
   ```  
2️⃣ **Select a script** to execute.  
3️⃣ **Follow the on-screen prompts** to analyze or patch an APK.  
4️⃣ *(Optional)* Clean up **temporary files** to free up space.  

---

## ⚡ Examples  

### **1️⃣ Quick Frida Injection Flow**  
```bash
python main.py
# => [Select "Frida Gadget Injector"]
# => [Pick target APK]
# => [Wait for patching & signing]
# => Done! Final patched APK saved in ./output
```  

### **2️⃣ Extract Strings from an APK**  
```bash
python string_extraction.py my_app.apk
# => Extracts strings from all files
# => Saves to: src/output/my_app_EXTRACTED/strings.csv
```  

### **3️⃣ Detect Malware Indicators in an APK**  
```bash
python malicious_indicator_detection.py
# => Select extracted strings CSV
# => Scans for obfuscation, C2 URLs, permissions, etc.
# => Saves results in: src/output/potential_indicators.csv
```  

---

## 🚧 Roadmap  

- [ ] **Support additional hooking frameworks**  
- [ ] **Multi-DEX patching capabilities**  
- [ ] **Enhanced logging & error handling**  
- [ ] **Docker support for isolated analysis**  

---

## 🤝 Contributing  

🔥 **Want to contribute?** Follow these steps:  

1️⃣ **Fork** the repository.  
2️⃣ **Create** a new feature branch:  
   ```bash
   git checkout -b feature/my-new-feature
   ```  
3️⃣ **Commit** your changes:  
   ```bash
   git commit -m "Added a new feature"
   ```  
4️⃣ **Push** to GitHub:  
   ```bash
   git push origin feature/my-new-feature
   ```  
5️⃣ **Open** a **Pull Request**! 🎉  

---

## 📜 License  

This project is **licensed** under the **MIT License**.  
See [`LICENSE`](LICENSE) for details.  

---

## ⚠ Disclaimer  

> **This toolkit is for educational and research purposes only.**  
> **Do NOT use it on apps you do not have explicit permission to modify.**  
> The maintainers assume **NO responsibility** for misuse or damage.  

---

### 🚀 **Happy Hacking!** 🔥  

For suggestions, issues, or feedback, feel free to open an [issue](https://github.com/L0WK3Y-IAAN/Mobile-RE-Toolkit/issues) or submit a pull request!  

