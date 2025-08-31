# 🧩 UIer

**UIer** is a minimalist personal widget app for displaying date, day of the week, and time on your Windows desktop.

Built with **Python (PyQt5)**, the widget floats on the desktop with a frameless transparent interface, stays behind other windows, and is fully customizable.

Developed by **Roman Martyniuk**

---

## 💡 Features

- Displays current **time**, **date**, and **weekday**.
- Transparent, frameless, always-on-desktop window.
- Close the widget using the `Esc` key.
- Choose fonts, text sizes, and screen position.
- Settings window available via system tray icon.
- Supports custom fonts (e.g., *Anurati*).

---

## 🖼 UI Preview

*(Add screenshots here if you'd like — for example, in an `img/` folder)*

---

## 🚀 How to Run

1. Install dependencies:
   
   ```bash
   pip install -r requirements.txt
   
3. Run the app:
   
python UIer.py

---

## 🛠 Build .exe (Windows)
1. Install PyInstaller:
   
    pip install pyinstaller
   
2. Run build command:
   
pyinstaller --onefile --windowed ^
  --add-data "fonts;fonts" ^
  --add-data "icon;icon" ^
  main.py

Make sure the fonts/ and icon/ folders are in the same directory as main.py. The path fonts;fonts means "include the contents of the fonts folder and place it in a fonts folder inside the executable"

---

## 📁 Project Structure

UIer/
├── Uier.py               # main script
├── fonts/
│   └── Anurati-Regular.otf
├── icon/
│   └── Logo.ico
├── README.md
├── requirements.txt

---

## 📦 requirements.txt
PyQt5

---

## 📜 License

This project is open for personal and public use under the following conditions:

You are free to use and modify the code.
You may include it in your own projects.
You must credit the original author: Roman Martyniuk.
Do not claim this code or modified versions as your original work.
If you fork the repository or share your version, please mention the original project or link back to it.

---

## ✍️ Author
**Roman Martyniuk** (aka *Roma_Doma*)

Originally created as a personal utility for customizing the Windows desktop.
