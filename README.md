# 🧩 UIer

**UIer** is a minimalist personal widget app for displaying the **date**, **day of the week**, and **time** on your Windows desktop.

Built with **Python + PyQt5**, the widget floats on the desktop with a **frameless**, **transparent** interface, stays behind other windows, and is fully customizable.

Developed by **Roman Martyniuk**.

---

## 💡 Features

- 🕒 Displays current **time**, **date**, and **weekday**
- 🪟 Transparent, frameless, always-on-desktop window
- ⌨️ Close the widget using the `Esc` key
- 🖋 Choose fonts, text sizes, and screen position
- ⚙️ Settings window available via system tray icon
- 🔤 Supports custom fonts (e.g., *Anurati*)

---

## 🖼 UI Preview

*(You can add screenshots here in an `img/` folder)*

---

## 🚀 How to Run

1. 📦 Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

2. ▶️ Run the app:

    ```bash
    python UIer.py
    ```

---

## 🛠 How to Build .exe (Windows)

1. 📥 Install PyInstaller:

    ```bash
    pip install pyinstaller
    ```

2. 🏗 Build with:

    ```bash
    pyinstaller --onefile --windowed ^
      --add-data "fonts;fonts" ^
      --add-data "icon;icon" ^
      UIer.py
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
