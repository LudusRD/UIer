import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QComboBox,
    QSpinBox, QPushButton, QSystemTrayIcon, QMenu, QAction
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QFontDatabase, QIcon


class WidgetApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_OpaquePaintEvent)

        self.day_label = QLabel("", self)
        self.day_label.setAlignment(Qt.AlignCenter)
        self.day_label.setStyleSheet("color: white;")

        self.date_label = QLabel("", self)
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setStyleSheet("color: white;")

        self.time_label = QLabel("", self)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("color: white;")

        layout = QVBoxLayout()
        layout.addWidget(self.day_label)
        layout.addWidget(self.date_label)
        layout.addWidget(self.time_label)
        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        self.setGeometry(100, 100, 400, 300)

    def update_time(self):
        current_time = time.strftime("%H:%M")
        current_day = time.strftime("%A")
        current_date_num = time.strftime("%d")
        current_date_month = time.strftime("%B").lower()

        spaced_day = '  '.join(current_day.upper())
        self.day_label.setText(spaced_day)
        self.date_label.setText(f"{current_date_num} {current_date_month}")
        self.time_label.setText(f"- {current_time.upper()} -")

    def apply_settings(self, fonts, sizes, position, offset_x=0, offset_y=0):
        self.day_label.setFont(QFont(fonts['day'], sizes['day']))
        self.date_label.setFont(QFont(fonts['date'], sizes['date']))
        self.time_label.setFont(QFont(fonts['time'], sizes['time']))

        for label in [self.day_label, self.date_label, self.time_label]:
            label.adjustSize()
            label.setAlignment(Qt.AlignCenter)

        self.adjustSize()  # ключевая строка — обновить размеры окна под содержимое
        self.repaint()
        self.resize(self.sizeHint())


        screen = QApplication.primaryScreen().geometry()
        screen_width, screen_height = screen.width(), screen.height()
        w, h = self.width(), self.height()

        pos = position
        if pos == "Top-left":
            x, y = 0, 0
        elif pos == "Top-center":
            x, y = (screen_width - w) // 2, 0
        elif pos == "Top-right":
            x, y = screen_width - w, 0
        elif pos == "Bottom-left":
            x, y = 0, screen_height - h
        elif pos == "Bottom-center":
            x, y = (screen_width - w) // 2, screen_height - h
        elif pos == "Bottom-right":
            x, y = screen_width - w, screen_height - h
        elif pos == "Left-center":
            x, y = 0, (screen_height - h) // 2
        elif pos == "Right-center":
            x, y = screen_width - w, (screen_height - h) // 2
        else:
            x, y = 0, 0


        x += offset_x
        y += offset_y

        self.move(x, y)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


class SettingsWindow(QWidget):
    def __init__(self, widget_app):
        super().__init__()
        self.widget_app = widget_app

        self.available_fonts = ["Arial", "Segoe UI", "Verdana", "Courier New"]

        font_path = r"C:\Users\25roma\source\repos\Uier\Uier\fonts\Anurati-Regular.otf"
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            anurati_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            self.available_fonts.insert(0, anurati_family)
        else:
            anurati_family = "Arial"

        self.init_ui(anurati_family)
        self.apply_clicked()

    def init_ui(self, anurati_family):
        self.setWindowTitle("Settings")
        layout = QVBoxLayout()

        self.font_selector_day = QComboBox(self)
        self.font_selector_day.addItems(self.available_fonts)
        self.font_selector_day.setCurrentText(anurati_family)
        layout.addWidget(self.font_selector_day)

        self.font_selector_date = QComboBox(self)
        self.font_selector_date.addItems(self.available_fonts)
        self.font_selector_date.setCurrentText("Verdana")
        layout.addWidget(self.font_selector_date)

        self.font_selector_time = QComboBox(self)
        self.font_selector_time.addItems(self.available_fonts)
        self.font_selector_time.setCurrentText("Verdana")
        layout.addWidget(self.font_selector_time)

        self.size_selector_day = QSpinBox(self)
        self.size_selector_day.setRange(8, 48)
        self.size_selector_day.setValue(40)
        layout.addWidget(self.size_selector_day)

        self.size_selector_date = QSpinBox(self)
        self.size_selector_date.setRange(8, 48)
        self.size_selector_date.setValue(21)
        layout.addWidget(self.size_selector_date)

        self.size_selector_time = QSpinBox(self)
        self.size_selector_time.setRange(8, 48)
        self.size_selector_time.setValue(15)
        layout.addWidget(self.size_selector_time)

        self.position_selector = QComboBox(self)
        self.position_selector.addItems([
            "Top-left", "Top-center", "Top-right",
            "Bottom-left", "Bottom-center", "Bottom-right",
            "Left-center", "Right-center"
        ])
        self.position_selector.setCurrentText("Top-center")
        layout.addWidget(self.position_selector)

        self.offset_x_spin = QSpinBox(self)
        self.offset_x_spin.setRange(-500, 500)
        self.offset_x_spin.setValue(0)
        layout.addWidget(self.offset_x_spin)

        self.offset_y_spin = QSpinBox(self)
        self.offset_y_spin.setRange(-500, 500)
        self.offset_y_spin.setValue(50)
        layout.addWidget(self.offset_y_spin)

        self.apply_button = QPushButton("Apply", self)
        self.apply_button.clicked.connect(self.apply_clicked)
        layout.addWidget(self.apply_button)

        self.finish_button = QPushButton("Finish", self)
        self.finish_button.clicked.connect(self.finish_clicked)
        layout.addWidget(self.finish_button)

        self.exit_button = QPushButton("Exit", self)
        self.exit_button.clicked.connect(self.close)
        layout.addWidget(self.exit_button)

        self.setLayout(layout)
        self.setGeometry(1350, 300, 400, 500)

        self.show()

    def apply_clicked(self):
        fonts = {
            'day': self.font_selector_day.currentText(),
            'date': self.font_selector_date.currentText(),
            'time': self.font_selector_time.currentText(),
        }
        sizes = {
            'day': self.size_selector_day.value(),
            'date': self.size_selector_date.value(),
            'time': self.size_selector_time.value(),
        }
        position = self.position_selector.currentText()
        offset_x = self.offset_x_spin.value()
        offset_y = self.offset_y_spin.value()

        QTimer.singleShot(0, lambda: self.widget_app.apply_settings(
            fonts, sizes, position, offset_x, offset_y
        ))
        self.widget_app.update_time()

    def finish_clicked(self):
        self.hide()


def main():
    app = QApplication(sys.argv)
    widget_app = WidgetApp()
    settings_window = SettingsWindow(widget_app)

    tray_icon = QSystemTrayIcon()
    tray_icon.setIcon(QIcon(r"C:\Users\25roma\source\repos\Uier\Uier\icon\Logo.ico"))
    tray_icon.setVisible(True)

    tray_menu = QMenu()

    action_show = QAction("Show", tray_menu)
    action_show.triggered.connect(widget_app.show)
    tray_menu.addAction(action_show)

    action_hide = QAction("Hide", tray_menu)
    action_hide.triggered.connect(widget_app.hide)
    tray_menu.addAction(action_hide)

    action_settings = QAction("Settings", tray_menu)
    action_settings.triggered.connect(settings_window.show)
    tray_menu.addAction(action_settings)

    action_exit = QAction("Close program", tray_menu)
    action_exit.triggered.connect(app.quit)
    tray_menu.addAction(action_exit)

    tray_icon.setContextMenu(tray_menu)

    tray_icon.activated.connect(
        lambda reason: widget_app.show() if reason == QSystemTrayIcon.DoubleClick else None
    )
    widget_app.update_time()

    widget_app.show()

    # Основной apply после запуска окна
    def post_launch_apply():
        settings_window.apply_clicked()
        widget_app.update_time()

    QTimer.singleShot(300, post_launch_apply)

    sys.exit(app.exec_())




if __name__ == "__main__":
    main()
