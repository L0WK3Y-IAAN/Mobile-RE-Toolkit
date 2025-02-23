# 🔥 Auto Frida Patcher

**Automate the Injection of Frida Gadget into Android APKs**  

🔹 **Author**: L0WK3Y  
🔹 **Category**: Mobile Reverse Engineering / Dynamic Instrumentation  
🔹 **License**: MIT  

---

## 🎯 Overview  

The **Auto Frida Patch** script automates the process of injecting Frida Gadget into an Android APK for **dynamic instrumentation**. It:  

✅ Fetches the latest **Frida version** dynamically from GitHub  
✅ Detects `.apk` files in both the **root** and `src/` folder  
✅ Automatically downloads and **decompresses** Frida Gadget  
✅ Decompiles the APK with **apktool**, injects Frida, and **rebuilds** it  
✅ **Creates a keystore** for signing if none exists  
✅ Signs the APK using **apksigner** (or `jarsigner` fallback)  
✅ **Cleans up temporary files** after completion (optional)  

This tool is useful for **Android pentesting**, **malware analysis**, and **reverse engineering**.  

---

## 🛠️ Prerequisites  

Ensure the following are installed and available in your system's `$PATH`:  

### 📌 **Required Dependencies**  
- **Python 3.x**  
- `colorama` for colored CLI output  
  ```sh
  pip install colorama
  ```
- `apktool` for decompiling and rebuilding APKs  
- `adb` for detecting the Android architecture  
- `keytool` for keystore management  
- `apksigner` or `jarsigner` for signing APKs  
- `zipalign` (optional) for aligning APKs  



---

## 🔧 Usage  

### **Run the Script**  
To patch an APK with Frida Gadget:  

```sh
python auto_frida_patch.py
```

### **What It Does**  

1. **Checks for dependencies** (`apktool`, `adb`, `keytool`, etc.)  
2. **Fetches the latest Frida version** from GitHub  
3. **Detects Android CPU architecture** via ADB  
4. **Downloads & extracts the correct Frida Gadget** binary  
5. **Lists available APKs** for the user to choose from  
6. **Decompiles the APK**, injects Frida, and **rebuilds** it  
7. **Signs the modified APK** using a keystore  
8. **Offers to clean up** temporary files  

---

## 🔍 Example Output  

```sh
[*] Checking latest Frida version via GitHub API: https://api.github.com/repos/frida/frida/releases/latest
[+] Latest Frida version: 16.6.8
[*] Detecting device ABI...
[+] Device ABI: arm64-v8a
[*] Downloading Frida Gadget...
[+] Download complete: src/output/frida-gadget-16.6.8-android-arm64.so
[*] APKs found in root/src:
   1. src/com.example.app.apk
[?] Which APK to patch? Enter a number: 1
[+] Selected APK: src/com.example.app.apk
[*] Decompiling APK with apktool...
[+] Frida Gadget injected into APK!
[*] Rebuilding APK...
[*] Signing the APK...
[+] Signed APK: src/output/signed_app_patched.apk
[✓] Done! Install with:
   adb install -r src/output/signed_app_patched.apk
```

---

## ⚙️ Advanced Features  

### **Keystore Management**  
- If no keystore exists, it will **automatically create one**.  
- Uses **keytool** to generate a keystore at:  
  ```
  src/output/my-release-key.jks
  ```
- Keystore credentials:  
  ```
  Alias: mykeyalias
  Password: my_password
  ```

### **Cleaning Up Temporary Files**  
After patching, the script **offers to remove**:  
- **Downloaded Frida Gadget files** (`.xz`, `.so`)  
- **Working directories** used by `apktool`  
- **Keystore** (if created automatically)  

To skip cleanup, simply **decline the prompt**.  

---

## 🏴‍☠️ Use Cases  

✅ **Pentesting** – Patch applications with Frida for runtime instrumentation  
✅ **Reverse Engineering** – Inject hooks and analyze app behavior dynamically  
✅ **CTF Challenges** – Bypass anti-tampering protections in APKs  
✅ **Security Research** – Explore app internals with Frida hooks  

---

## 🛠️ Troubleshooting  

### ❌ **Error: "No .apk files found!"**  
🔹 **Fix:** Move your APK into the root or `src/` folder and rerun the script.  

### ❌ **Error: "Missing required tool 'apktool' in PATH."**  
🔹 **Fix:** Install the missing tool and ensure it's available in your `$PATH`.  

```sh
sudo apt install apktool  # Linux
brew install apktool      # macOS
choco install apktool     # Windows
```

### ❌ **Error: "adb not found"**  
🔹 **Fix:** Install **Android Platform Tools** and ensure ADB is accessible.  

```sh
sudo apt install android-tools-adb  # Linux
brew install android-platform-tools # macOS
```

---

## 📜 License  
This project is licensed under the **MIT License** – feel free to modify and use it as needed.  

---

## 🤝 Contributing  
💡 **Want to improve this tool?** Open an issue or submit a pull request!  



Happy Patching! 🚀