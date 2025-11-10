# 🧩 UIer

**UIer** is a minimalist personal widget app for displaying the **date**, **day of the week**, and **time** on your Windows desktop.

It also includes a **task manager** where you can add tasks, rename them, delete them, reorder by drag and drop, and mark tasks as completed.

Built with **Python + PyQt5**, the widget floats on the desktop with a **frameless**, **transparent** interface, stays behind other windows, and is fully customizable.

Developed by **Roman Martyniuk**.

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
- 🗔 Adjustable **screen offsets** for precise placement

---

## 🖼 UI Preview

<img width="480" height="233" alt="Clock" src="https://github.com/user-attachments/assets/2eb8bafb-bc94-4e92-be5b-7d2a8a0cb863" />
<img width="480" height="560" alt="Task manager" src="https://github.com/user-attachments/assets/c7e76e95-c638-40b3-8e18-0cfe531f1acd" />
<img width="480" height="250" alt="Calendar" src="https://github.com/user-attachments/assets/71ba9d01-0dd8-4937-b79e-1f1bf4138d67" />




---

## 🚀 How to Run

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

1. 📥 Install PyInstaller:

    ```bash
    pip install pyinstaller
    ```

2. 🏗 Build with:

> PowerShell

```bash
pyinstaller --onefile --windowed --icon=icon\Logo.ico --add-data "fonts;fonts" --add-data "icon;icon" Uier.py
```
    
> CMD

```bash
pyinstaller --onefile --windowed ^
  --icon=icon\Logo.ico ^
  --add-data "fonts;fonts" ^
  --add-data "icon;icon" ^
  Uier.py
```

💡 Make sure the `fonts/` and `icon/` folders are in the same directory as `UIer.py`.

👉 The `--add-data "fonts;fonts"` argument means: *“include everything inside the `fonts/` folder and place it in a folder called `fonts` inside the built executable.”*

---

## 📁 Project Structure

```bash
UIer/
├── Uier.py               # 🧠main script
├── fonts/
│   └── Anurati-Regular.otf
├── icon/
│   └── Logo.ico
├── README.md
├── requirements.txt
```

---

## 📦 requirements.txt
PyQt5
recurring-ical-events


```bash
# Minimal version (works with PyQt5 5.12 and above)
PyQt5 - 5.12+

# Recommended fixed version (latest stable as of August 2025)
PyQt5 - 5.15.11
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

Originally created as a personal utility to customize and beautify the Windows desktop.
