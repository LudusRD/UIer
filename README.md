# 🧩 UIer
**UIer** is a minimalist personal widget app for displaying the **date**, **day of the week**, and **time** on your Windows desktop.
It also includes a **task manager** where you can add tasks, rename them, delete them, reorder by drag and drop, and mark tasks as completed.
Built with **Python + PyQt5 + Ical**, the widget floats on the desktop with a **frameless**, **transparent** interface, stays behind other windows, and is fully customizable.

---

## 💡 Features
- 🕒 Displays current **time**, **date**, and **weekday**
- 🪟 Transparent, frameless, always-on-desktop window
- 🖋 Choose fonts, text sizes, and screen position
- ⚙️ Settings window available via system tray icon
- 🔤 Supports custom fonts (e.g., *Anurati*)
- ✅ **Task manager** with add, remove, and edit functionality
- 🔼🔽 Reorder tasks using **up/down buttons** or **drag & drop**
- ✏️ Edit tasks via **double-click**
- 💾 Tasks **persist across sessions** using QSettings (JSON storage)
- 🖱 System tray integration with **show/hide clock**, **show/hide tasks**, and **settings** options
- 📅 **Calendar widget** showing upcoming events from a `.ics` URL, with all-day event support and navigation
- 🗔 Adjustable **screen offsets** for precise placement

---

## 🖼 UI Preview
<img width="480" height="233" alt="Clock" src="https://github.com/user-attachments/assets/2eb8bafb-bc94-4e92-be5b-7d2a8a0cb863" />
<img width="480" height="560" alt="Task manager" src="https://github.com/user-attachments/assets/c7e76e95-c638-40b3-8e18-0cfe531f1acd" />
<img width="480" height="250" alt="Calendar" src="https://github.com/user-attachments/assets/71ba9d01-0dd8-4937-b79e-1f1bf4138d67" />

---

## 🚀 Installation & Launch

### For Users
1. Go to the [Releases](https://github.com/LudusRD/UIer/releases) page.
2. Download the latest `Uier_Setup_v1.0.0.exe`.
3. Run the installer and follow the instructions.

### For Developers (Run from source)
1. 📦 Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2. ▶️ Run the app:
    ```bash
    python Uier.py
    ```

---

## 🛠 How to Build .exe (Windows)

### 1. Build .exe (PyInstaller)
1. 📥 Install PyInstaller:
    ```bash
    pip install pyinstaller
    ```
2. 🧹 **Important:** If you had build errors before, delete `build/` and `dist/` folders.
3. 🏗 Build using the spec file:
    ```bash
    pyinstaller --clean Uier.spec
    ```
    *Note: The `.spec` file is pre-configured to include `hiddenimports` and resource folders.*

### 2. Create Installer (Inno Setup)
To create a professional single-file setup:
1. Open the included `.iss` script in **Inno Setup**.
2. Ensure you have successfully built the `.exe` in the `dist/` folder first.
3. Click **Compile**. The finished installer will appear in your output directory.

---

## 📁 Project Structure

```
UIer/
├── Uier.py                   # 🧠 Main script
├── Uier.spec                 # 🔧 PyInstaller build config
├── fonts/
│   └── Anurati-Regular.otf
├── icon/
│   └── Logo.ico
├── README.md
├── requirements.txt
```

---

## 📦 requirements.txt

```
PyQt5
recurring-ical-events
icalendar
```

---

## 📜 License

This project is open for **personal and public use**, with a few simple conditions:

- ✅ You **may use and modify** the code freely  
- ✅ You **may include it** in your own projects  
- ❗ You **must credit** the original author: **Roman Martyniuk**  
- ❌ Do **not** claim this code or modified versions as your own  
- 🔗 If you fork or share this project, please link back to the original repository

---

## ✍️ Author

**Roman Martyniuk** (aka *Roma_Doma*)  
Originally created as a personal utility to customize and beautify the Windows desktop. AI was used to adjust the code and comments to a single style.
