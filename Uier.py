import sys
import time
import json
from functools import partial
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QComboBox,
    QSpinBox, QPushButton, QSystemTrayIcon, QMenu, QAction,
    QLineEdit, QListWidget, QListWidgetItem, QHBoxLayout,
    QInputDialog, QAbstractItemView
)
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtGui import QFont, QFontDatabase, QIcon


class TaskRow(QWidget):
    """One row in the task list: label + buttons."""
    def __init__(self, text, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.label = QLabel(text)
        layout.addWidget(self.label)

        self.btn_up = QPushButton("⬆")
        self.btn_up.setFixedSize(30, 25)
        layout.addWidget(self.btn_up)

        self.btn_down = QPushButton("⬇")
        self.btn_down.setFixedSize(30, 25)
        layout.addWidget(self.btn_down)

        self.btn_done = QPushButton("✅")
        self.btn_done.setFixedSize(30, 25)
        layout.addWidget(self.btn_done)

        layout.setContentsMargins(0, 0, 0, 0)


class TaskListWidget(QListWidget):
    """QListWidget with a drop-complete notification (used to update task order)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # anable internal drag & drop
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self._drop_callback = None

    def set_drop_callback(self, fn):
        self._drop_callback = fn

    def dropEvent(self, event):
        # first let the default behavior reorder items
        super().dropEvent(event)
        # then call the callback so self.tasks can be synchronized
        if callable(self._drop_callback):
            self._drop_callback()


class TaskWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.layout = QVBoxLayout()

        # Field for adding a new task
        input_layout = QHBoxLayout()
        self.task_input = QLineEdit(self)
        self.task_input.setPlaceholderText("Enter a task...")
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_task)
        input_layout.addWidget(self.task_input)
        input_layout.addWidget(self.add_button)

        self.layout.addLayout(input_layout)

        # Task list (custom version with drag &drop callback)
        self.task_list = TaskListWidget(self)
        self.task_list.set_drop_callback(self.on_internal_move)
        # double-click to edit
        self.task_list.itemDoubleClicked.connect(self.edit_task_item)
        self.layout.addWidget(self.task_list)

        self.setLayout(self.layout)
        self.setGeometry(50, 350, 360, 420)

        # internal storage for tasks: list of dicts with unique id and text
        self.tasks = []  # example: [{'id': 1, 'text': 'Do X'}, ...]
        self._next_id = 1

        # Load tasks from settings (if any) and display immediately
        self.load_tasks()
        self.rebuild_list()

    # ---------------------------
    # Task and UI management
    # ---------------------------
    def add_task(self):
        text = self.task_input.text().strip()
        if not text:
            return
        task = {'id': self._next_id, 'text': text}
        self._next_id += 1
        self.tasks.append(task)
        self.task_input.clear()
        self.rebuild_list()
        self.save_tasks()

    def rebuild_list(self):
        """Rebuild the QListWidget based on self.tasks.
        First safely remove old widgets, then create new ones."""
        # safely remove all items and widgets
        while self.task_list.count() > 0:
            it = self.task_list.item(0)
            w = self.task_list.itemWidget(it)
            taken = self.task_list.takeItem(0)
            if w is not None:
                # detach and mark for deletion
                w.setParent(None)
                w.deleteLater()
            del taken

        # then add new items in the same order
        for task in self.tasks:
            item = QListWidgetItem()
            row_widget = TaskRow(task['text'])
            # auxiliary field for debugging/identification
            row_widget.task_id = task['id']

            item.setSizeHint(row_widget.sizeHint())
            self.task_list.addItem(item)
            self.task_list.setItemWidget(item, row_widget)

            # Connect signals to functions that operate by task_id
            row_widget.btn_done.clicked.connect(partial(self.remove_task_by_id, task['id']))
            row_widget.btn_up.clicked.connect(partial(self.move_task_by_id, task['id'], -1))
            row_widget.btn_down.clicked.connect(partial(self.move_task_by_id, task['id'], 1))

    def find_index_by_id(self, task_id):
        for idx, t in enumerate(self.tasks):
            if t['id'] == task_id:
                return idx
        return -1

    def remove_task_by_id(self, task_id):
        idx = self.find_index_by_id(task_id)
        if idx == -1:
            return
        self.tasks.pop(idx)
        self.rebuild_list()
        self.save_tasks()

    def move_task_by_id(self, task_id, direction):
        """direction: -1 (up), +1 (down)."""
        idx = self.find_index_by_id(task_id)
        if idx == -1:
            return
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self.tasks):
            return
        # reorder in the data list
        self.tasks.insert(new_idx, self.tasks.pop(idx))
        self.rebuild_list()
        self.save_tasks()

    # ---------------------------
    # Drag & Drop: synvhronize order after internal move
    # ---------------------------
    def on_internal_move(self):
        """Called after UI-internal move of items — rebuild self.tasks from the visual order."""
        new_tasks = []
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            w = self.task_list.itemWidget(item)
            if w is not None and hasattr(w, 'task_id'):
                # find the corresponding task by id (in case text was edited)
                t = next((x for x in self.tasks if x['id'] == w.task_id), None)
                if t is not None:
                    # update text from the widget (if edited)
                    t['text'] = w.label.text()
                    new_tasks.append(t)
        # replace the order and save
        self.tasks = new_tasks
        self.save_tasks()
        # rebuild to ensure signals are correctly wired (avoid duplicates)
        self.rebuild_list()

    # ---------------------------
    # Double-click editing
    # ---------------------------
    def edit_task_item(self, item: QListWidgetItem):
        """Open an edit dialog when an item is double-clicked."""
        w = self.task_list.itemWidget(item)
        if w is None:
            return
        current_text = w.label.text()
        new_text, ok = QInputDialog.getText(self, "Edit task", "Task:", QLineEdit.Normal, current_text)
        if ok:
            new_text = new_text.strip()
            if new_text == "":
                # if cleared — remove the task
                if hasattr(w, 'task_id'):
                    self.remove_task_by_id(w.task_id)
                return
            # update widget and data
            w.label.setText(new_text)
            if hasattr(w, 'task_id'):
                idx = self.find_index_by_id(w.task_id)
                if idx != -1:
                    self.tasks[idx]['text'] = new_text
                    self.save_tasks()

    # ---------------------------
    # Save / Load (QSetings, JSON)
    # ---------------------------
    def save_tasks(self):
        settings = QSettings("MyCompany", "MyWidgetApp")
        try:
            settings.setValue("tasks", json.dumps(self.tasks, ensure_ascii=False))
        except Exception:
            # fallback: save as a plain list of texts
            settings.setValue("tasks", json.dumps([t['text'] for t in self.tasks], ensure_ascii=False))

    def load_tasks(self):
        settings = QSettings("MyCompany", "MyWidgetApp")
        raw = settings.value("tasks", "")
        if raw is None or raw == "":
            self.tasks = []
            return
        try:
            data = json.loads(raw)
            # support old format: list of strings
            if isinstance(data, list) and all(isinstance(x, str) for x in data):
                self.tasks = []
                for text in data:
                    self.tasks.append({'id': self._next_id, 'text': text})
                    self._next_id += 1
            elif isinstance(data, list) and all(isinstance(x, dict) for x in data):
                # ensure each task has an id (create one if missing)
                self.tasks = []
                for entry in data:
                    if 'id' in entry and isinstance(entry['id'], int):
                        tid = entry['id']
                    else:
                        tid = self._next_id
                        self._next_id += 1
                    text = entry.get('text', '')
                    self.tasks.append({'id': tid, 'text': text})
                    if tid >= self._next_id:
                        self._next_id = tid + 1
            else:
                self.tasks = []
        except Exception:
            # if parsing fails — clear
            self.tasks = []

    # ---------------------------
    # Legacy methods (kept for compatibility)
    # ---------------------------
    def _remove_item(self, item: QListWidgetItem, widget: QWidget):
        """Deprecated method — kept for compatibility."""
        row = self.task_list.row(item)
        if row < 0:
            return
        w = self.task_list.itemWidget(item)
        taken = self.task_list.takeItem(row)
        if w is not None:
            w.setParent(None)
            w.deleteLater()
        try:
            del taken
        except Exception:
            pass

    def move_item(self, item: QListWidgetItem, direction: int):
        """Deprecated direct swap of widgets — not recommended."""
        row = self.task_list.row(item)
        if row == -1:
            return
        new_row = row + direction
        count = self.task_list.count()
        if new_row < 0 or new_row >= count:
            return

        other_item = self.task_list.item(new_row)
        if other_item is None:
            return

        w1 = self.task_list.itemWidget(item)
        w2 = self.task_list.itemWidget(other_item)

        if w1 is None and w2 is None:
            return

        self.task_list.setItemWidget(item, w2)
        self.task_list.setItemWidget(other_item, w1)

        if w1 is not None:
            item.setSizeHint(w1.sizeHint())
        if w2 is not None:
            other_item.setSizeHint(w2.sizeHint())

        self.task_list.setCurrentItem(other_item if direction == -1 else item)


# ---------------------------
# The rest of the code (unchanged except we show the task window immediately)
# ---------------------------
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
        current_date_month = time.strftime("%B")

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

        self.adjustSize()
        self.repaint()
        self.resize(self.sizeHint())

        self.layout().invalidate()
        self.layout().activate()
        self.updateGeometry()

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

        x = max(0, min(x, screen_width - w))
        y = max(0, min(y, screen_height - h))

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
        self.load_settings()
        self.apply_clicked()

    def init_ui(self, anurati_family):
        self.setWindowTitle("Settings")
        layout = QVBoxLayout()

        self.font_selector_day = QComboBox(self)
        self.font_selector_day.addItems(self.available_fonts)
        layout.addWidget(self.font_selector_day)

        self.font_selector_date = QComboBox(self)
        self.font_selector_date.addItems(self.available_fonts)
        layout.addWidget(self.font_selector_date)

        self.font_selector_time = QComboBox(self)
        self.font_selector_time.addItems(self.available_fonts)
        layout.addWidget(self.font_selector_time)

        self.size_selector_day = QSpinBox(self)
        self.size_selector_day.setRange(8, 48)
        layout.addWidget(self.size_selector_day)

        self.size_selector_date = QSpinBox(self)
        self.size_selector_date.setRange(8, 48)
        layout.addWidget(self.size_selector_date)

        self.size_selector_time = QSpinBox(self)
        self.size_selector_time.setRange(8, 48)
        layout.addWidget(self.size_selector_time)

        self.position_selector = QComboBox(self)
        self.position_selector.addItems([
            "Top-left", "Top-center", "Top-right",
            "Bottom-left", "Bottom-center", "Bottom-right",
            "Left-center", "Right-center"
        ])
        layout.addWidget(self.position_selector)

        self.offset_x_spin = QSpinBox(self)
        self.offset_x_spin.setRange(-500, 500)
        layout.addWidget(self.offset_x_spin)

        self.offset_y_spin = QSpinBox(self)
        self.offset_y_spin.setRange(-500, 500)
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
        self.save_settings()

    def save_settings(self):
        settings = QSettings("MyCompany", "MyWidgetApp")

        settings.setValue("fonts/day", self.font_selector_day.currentText())
        settings.setValue("fonts/date", self.font_selector_date.currentText())
        settings.setValue("fonts/time", self.font_selector_time.currentText())

        settings.setValue("sizes/day", self.size_selector_day.value())
        settings.setValue("sizes/date", self.size_selector_date.value())
        settings.setValue("sizes/time", self.size_selector_time.value())

        settings.setValue("position", self.position_selector.currentText())
        settings.setValue("offset_x", self.offset_x_spin.value())
        settings.setValue("offset_y", self.offset_y_spin.value())

    def load_settings(self):
        settings = QSettings("MyCompany", "MyWidgetApp")

        self.font_selector_day.setCurrentText(settings.value("fonts/day", self.available_fonts[0]))
        self.font_selector_date.setCurrentText(settings.value("fonts/date", "Verdana"))
        self.font_selector_time.setCurrentText(settings.value("fonts/time", "Verdana"))

        self.size_selector_day.setValue(int(settings.value("sizes/day", 40)))
        self.size_selector_date.setValue(int(settings.value("sizes/date", 21)))
        self.size_selector_time.setValue(int(settings.value("sizes/time", 15)))

        self.position_selector.setCurrentText(settings.value("position", "Top-center"))
        self.offset_x_spin.setValue(int(settings.value("offset_x", 0)))
        self.offset_y_spin.setValue(int(settings.value("offset_y", 50)))

    def finish_clicked(self):
        self.hide()


def main():
    app = QApplication(sys.argv)
    widget_app = WidgetApp()
    task_widget = TaskWidget()
    settings_window = SettingsWindow(widget_app)

    tray_icon = QSystemTrayIcon()
    tray_icon.setIcon(QIcon(r"C:\Users\25roma\source\repos\Uier\Uier\icon\Logo.ico"))
    tray_icon.setVisible(True)

    tray_menu = QMenu()

    action_show = QAction("Show Clock", tray_menu)
    action_show.triggered.connect(widget_app.show)
    tray_menu.addAction(action_show)

    action_hide = QAction("Hide Clock", tray_menu)
    action_hide.triggered.connect(widget_app.hide)
    tray_menu.addAction(action_hide)

    action_show_tasks = QAction("Show Tasks", tray_menu)
    action_show_tasks.triggered.connect(task_widget.show)
    tray_menu.addAction(action_show_tasks)

    action_hide_tasks = QAction("Hide Tasks", tray_menu)
    action_hide_tasks.triggered.connect(task_widget.hide)
    tray_menu.addAction(action_hide_tasks)

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

    # Show both windows immediatelly (so tasks are visible without extra actions)
    widget_app.show()
    task_widget.show()

    def post_launch_apply():
        settings_window.apply_clicked()
        widget_app.update_time()

    QTimer.singleShot(300, post_launch_apply)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
