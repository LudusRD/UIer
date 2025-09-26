import sys
import os
import time
import json
import recurring_ical_events
import datetime
import urllib.request
from functools import partial
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QComboBox,
    QSpinBox, QPushButton, QSystemTrayIcon, QMenu, QAction,
    QLineEdit, QListWidget, QListWidgetItem, QHBoxLayout,
    QInputDialog, QAbstractItemView, QMessageBox, QCheckBox,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtGui import QFont, QFontDatabase, QIcon

from icalendar import Calendar  # pip install icalendar

MAX_TASK_LENGTH = 26  # max chars for task text

# ---------------------------
# Visual constants / styles
# ---------------------------
DARK_BG = "#212121"
DARK_BTN_BG = "#2a2a2a"
DARK_BORDER = "#191919"
LIGHT_BORDER = "#dcdcdc"

BTN_BASE_PAD = "padding: 6px 10px; border-radius: 6px;"

ROW_BTN_DARK = f"""
color: white; background: transparent; border: 1px solid {DARK_BORDER}; border-radius: 4px;
"""

ROW_BTN_LIGHT = f"""
color: black; background: transparent; border: 1px solid {LIGHT_BORDER}; border-radius: 4px;
"""

PRIMARY_BTN_DARK = f"""
QPushButton {{
    color: white;
    background-color: {DARK_BTN_BG};
    border: 1px solid {DARK_BORDER};
    {BTN_BASE_PAD}
}}
"""
PRIMARY_BTN_DARK_HOVER = """
QPushButton:hover { background-color: #303030; }
QPushButton:pressed { background-color: #1f1f1f; }
"""

PRIMARY_BTN_LIGHT = f"""
QPushButton {{
    color: black;
    background-color: white;
    border: 1px solid {LIGHT_BORDER};
    {BTN_BASE_PAD}
}}
"""
PRIMARY_BTN_LIGHT_HOVER = """
QPushButton:hover { background-color: #f3f3f3; }
QPushButton:pressed { background-color: #e8e8e8; }
"""

LINEEDIT_DARK = f"color: white; background-color: {DARK_BTN_BG}; border: 1px solid {DARK_BORDER}; border-radius: 6px; padding: 6px;"
LINEEDIT_LIGHT = f"color: black; background-color: white; border: 1px solid {LIGHT_BORDER}; border-radius: 6px; padding: 6px;"

QMSGBOX_DARK = f"""
QMessageBox {{
    background-color: {DARK_BG};
}}
QLabel {{
    color: white;
}}
QPushButton, QDialogButtonBox QPushButton {{
    color: white;
    background-color: {DARK_BTN_BG};
    border: 1px solid {DARK_BORDER};
    padding: 6px 10px;
    border-radius: 6px;
}}
QPushButton:hover, QDialogButtonBox QPushButton:hover {{
    background-color: #303030;
}}
QPushButton:pressed, QDialogButtonBox QPushButton:pressed {{
    background-color: #1f1f1f;
}}
"""

QMSGBOX_LIGHT = f"""
QMessageBox {{
    background-color: white;
}}
QLabel {{
    color: black;
}}
QPushButton, QDialogButtonBox QPushButton {{
    color: black;
    background-color: white;
    border: 1px solid {LIGHT_BORDER};
    padding: 6px 10px;
    border-radius: 6px;
}}
QPushButton:hover, QDialogButtonBox QPushButton:hover {{
    background-color: #f3f3f3;
}}
QPushButton:pressed, QDialogButtonBox QPushButton:pressed {{
    background-color: #e8e8e8;
}}
"""

# ---------------------------
# Calendar widget (uses .ics URL)
# ---------------------------
class CalendarWidget(QWidget):
    def __init__(self):
        super().__init__()
        # window flags and transparency
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # main event label (single-line summary) and all-day label below
        self.main_label = QLabel("Loading...", self)
        self.main_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.main_label.setStyleSheet("color: white;")
        f = self.main_label.font()
        f.setPointSize(10)
        self.main_label.setFont(f)
        self.main_label.setContentsMargins(0, 0, 0, 0)
        self.main_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.allday_label = QLabel("", self)
        self.allday_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.allday_label.setStyleSheet("color: white;")
        fa = self.allday_label.font()
        fa.setPointSize(9)
        self.allday_label.setFont(fa)
        # hide by default and make it not take extra vertical space
        self.allday_label.setVisible(False)
        self.allday_label.setContentsMargins(0, 0, 0, 0)
        self.allday_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.allday_label.setMinimumHeight(0)

        # navigation controls: Prev / index / Next
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(6)

        # keep a small spacer to separate from right edge if needed
        nav_layout.addStretch()

        # make the buttons a bit smaller so they don't force extra vertical room
        btn_h, btn_w = 20, 30
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedSize(btn_w, btn_h)
        self.prev_btn.clicked.connect(self.prev_event)
        nav_layout.addWidget(self.prev_btn)

        self.index_label = QLabel("", self)
        self.index_label.setAlignment(Qt.AlignCenter)
        # smaller height so it doesn't add vertical gap
        self.index_label.setFixedHeight(18)
        self.index_label.setFixedWidth(60)
        self.index_label.setContentsMargins(0, 0, 0, 0)
        self.index_label.setStyleSheet("color: white; padding: 0px; margin: 0px;")
        nav_layout.addWidget(self.index_label)

        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedSize(btn_w, btn_h)
        self.next_btn.clicked.connect(self.next_event)
        nav_layout.addWidget(self.next_btn)

        # wrap nav_layout into a widget so we can add it to the vbox with alignment
        nav_widget = QWidget()
        nav_widget.setLayout(nav_layout)
        nav_widget.setContentsMargins(0, 0, 0, 0)
        nav_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        # main vertical layout: minimal spacing / margins to avoid gaps
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 2, 4, 2)   # small margins
        layout.setSpacing(2)                    # tight spacing
        layout.addWidget(self.main_label)
        layout.addWidget(self.allday_label)
        # add nav_widget aligned to the right (no extra vertical stretch)
        layout.addWidget(nav_widget, 0, Qt.AlignRight)
        self.setLayout(layout)

        self.setGeometry(1100, 970, 800, 140)

        self.theme = 'Day'

        # poll timer (will switch between fast retry and normal intervals)
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.update_event)
        self._retry_interval = 2_000
        self._normal_interval = 30_000

        self._loading = False

        # occurrences lists and current index
        self._events = []         # timed event occurrences
        self._allday_events = []  # all-day event titles
        self._event_index = 0

        # start polling with fast retry until first successful load
        self.poll_timer.start(self._retry_interval)
        QTimer.singleShot(0, self.update_event)

    def _load_ics_from_url(self, url: str) -> Calendar:
        """Download .ics data and parse with icalendar.Calendar."""
        with urllib.request.urlopen(url, timeout=8) as resp:
            data = resp.read()
        cal = Calendar.from_ical(data)
        return cal

    def _is_allday_occurrence(self, comp) -> bool:
        """Decide whether an occurrence is an all-day event.

        Heuristics:
          - dtstart is date-only -> all-day
          - or dtstart time == 00:00 and dtend time == 00:00 and duration >= 1 day -> all-day
        """
        try:
            start = comp.decoded('dtstart')
        except Exception:
            return False

        # date-only start -> all-day
        if isinstance(start, datetime.date) and not isinstance(start, datetime.datetime):
            return True

        # convert to datetime at midnight if needed
        if isinstance(start, datetime.datetime):
            start_dt = start
        else:
            start_dt = datetime.datetime.combine(start, datetime.time.min)

        # obtain end or duration
        end_dt = None
        try:
            end = comp.decoded('dtend')
            if isinstance(end, datetime.date) and not isinstance(end, datetime.datetime):
                end_dt = datetime.datetime.combine(end, datetime.time.min)
            else:
                end_dt = end
        except Exception:
            # fallback to duration
            try:
                dur = comp.decoded('duration')
                if isinstance(dur, datetime.timedelta):
                    end_dt = start_dt + dur
            except Exception:
                end_dt = None

        if isinstance(end_dt, datetime.datetime):
            if start_dt.time() == datetime.time.min and end_dt.time() == datetime.time.min:
                delta_days = (end_dt.date() - start_dt.date()).days
                if delta_days >= 1:
                    return True

        return False

    def _format_event_line(self, comp, now: datetime.datetime) -> str:
        """Format a single occurrence into a compact string without trailing commas."""
        # dtstart -> ensure datetime
        dt = comp.decoded('dtstart')
        if isinstance(dt, datetime.date) and not isinstance(dt, datetime.datetime):
            dt = datetime.datetime.combine(dt, datetime.time.min)

        # convert to local timezone if needed
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc).astimezone()
        else:
            dt = dt.astimezone()

        start_time_str = dt.strftime("%H:%M")

        # determine end time string (if available)
        end_time_str = None
        try:
            dtend = comp.decoded('dtend')
            if isinstance(dtend, datetime.date) and not isinstance(dtend, datetime.datetime):
                dtend = datetime.datetime.combine(dtend, datetime.time.min)
            if dtend is not None:
                if dtend.tzinfo is None:
                    dtend = dtend.replace(tzinfo=datetime.timezone.utc).astimezone()
                else:
                    dtend = dtend.astimezone()
                end_time_str = dtend.strftime("%H:%M")
        except Exception:
            end_time_str = None

        # fallback: duration
        if end_time_str is None:
            try:
                dur = comp.decoded('duration')
                if isinstance(dur, datetime.timedelta):
                    dt_end_guess = dt + dur
                    end_time_str = dt_end_guess.strftime("%H:%M")
            except Exception:
                end_time_str = None

        time_display = start_time_str if end_time_str is None else f"{start_time_str}-{end_time_str}"

        # make sure 'now' is timezone-aware
        if now.tzinfo is None:
            now = now.astimezone()

        delta = dt - now
        if delta.total_seconds() > 0:
            days, seconds = delta.days, delta.seconds
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            until_parts = []
            if days > 0:
                until_parts.append(f"{days}d")
            if hours > 0:
                until_parts.append(f"{hours}h")
            if minutes > 0:
                until_parts.append(f"{minutes}m")
            until_str = "in " + " ".join(until_parts) if until_parts else "in 0m"
        else:
            until_str = "ongoing"

        summary = comp.get('summary') or comp.get('name') or "No title"
        location = comp.get('location') or ""
        # keep only the first word of location to keep line compact (as before)
        short_location = " ".join(str(location).split()[:1]).rstrip(",")

        # build parts and join to avoid trailing commas when a part is empty
        parts = [str(summary).strip(), until_str.strip(), time_display.strip()]
        if short_location:
            parts.append(short_location.strip())

        return ", ".join(p for p in parts if p)

    def update_event(self):
        """Fetch calendar, split occurrences into timed and all-day, update UI."""
        if self._loading:
            return

        self._loading = True
        try:
            settings = QSettings("MyCompany", "MyWidgetApp")
            ics_url = settings.value("calendar_url", "", type=str).strip()
            if not ics_url:
                self.main_label.setText("Calendar URL not set")
                self.allday_label.setText("")
                self.allday_label.setVisible(False)
                self.poll_timer.setInterval(self._retry_interval)
                self._events = []
                self._allday_events = []
                self._event_index = 0
                self._update_nav_controls()
                return

            try:
                cal = self._load_ics_from_url(ics_url)
            except Exception as e:
                self.main_label.setText(f"Error loading calendar: {e}")
                self.allday_label.setText("")
                self.allday_label.setVisible(False)
                self.poll_timer.setInterval(self._retry_interval)
                self._events = []
                self._allday_events = []
                self._event_index = 0
                self._update_nav_controls()
                return

            # successful load -> use normal polling interval
            self.poll_timer.setInterval(self._normal_interval)

            now = datetime.datetime.now().astimezone()
            window_end = now + datetime.timedelta(days=7)

            occurrences = recurring_ical_events.of(cal).between(now, window_end)

            if not occurrences:
                self.main_label.setText("No upcoming events.")
                self.allday_label.setText("")
                self.allday_label.setVisible(False)
                self._events = []
                self._allday_events = []
                self._event_index = 0
                self._update_nav_controls()
                return

            # sort by start
            try:
                occurrences.sort(key=lambda e: e.decoded("dtstart"))
            except Exception:
                pass

            timed = []
            allday_titles = []
            for occ in occurrences:
                try:
                    if self._is_allday_occurrence(occ):
                        title = occ.get('summary') or occ.get('name') or "No title"
                        tstr = str(title).strip()
                        if tstr and tstr not in allday_titles:
                            allday_titles.append(tstr)
                    else:
                        timed.append(occ)
                except Exception:
                    timed.append(occ)

            self._events = timed
            self._allday_events = allday_titles

            # display current timed event if present
            if self._events:
                if not (0 <= self._event_index < len(self._events)):
                    self._event_index = 0
                cur = self._events[self._event_index]
                try:
                    self.main_label.setText(self._format_event_line(cur, now))
                except Exception:
                    self.main_label.setText(str(cur.get('summary') or "Event"))
            else:
                self._event_index = 0
                self.main_label.setText("No timed events in the next 7 days.")

            # format all-day list without trailing commas
            if self._allday_events:
                joined = ", ".join(self._allday_events)
                if len(joined) > 220:
                    joined = joined[:217] + "..."
                self.allday_label.setText("All-day: " + joined)
                self.allday_label.setVisible(True)
            else:
                self.allday_label.setText("")
                self.allday_label.setVisible(False)

            self._update_nav_controls()

        except Exception as e:
            self.main_label.setText(f"Error processing calendar: {e}")
            self.allday_label.setText("")
            self.allday_label.setVisible(False)
            self.poll_timer.setInterval(self._retry_interval)
            self._events = []
            self._allday_events = []
            self._event_index = 0
            self._update_nav_controls()
        finally:
            self._loading = False

    # ---------------------------
    # Navigation helpers
    # ---------------------------
    def _update_nav_controls(self):
        """Enable/disable Prev/Next and update the index label."""
        total = len(self._events)
        if total <= 1:
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
        else:
            self.prev_btn.setEnabled(self._event_index > 0)
            self.next_btn.setEnabled(self._event_index < total - 1)

        if total == 0:
            self.index_label.setText("")
        else:
            self.index_label.setText(f"{self._event_index+1} / {total}")

    def prev_event(self):
        """Show previous timed occurrence if available."""
        if not self._events:
            return
        if self._event_index > 0:
            self._event_index -= 1
            now = datetime.datetime.now().astimezone()
            try:
                self.main_label.setText(self._format_event_line(self._events[self._event_index], now))
            except Exception:
                self.main_label.setText(str(self._events[self._event_index].get('summary') or "Event"))
            self._update_nav_controls()

    def next_event(self):
        """Show next timed occurrence if available."""
        if not self._events:
            return
        if self._event_index < len(self._events) - 1:
            self._event_index += 1
            now = datetime.datetime.now().astimezone()
            try:
                self.main_label.setText(self._format_event_line(self._events[self._event_index], now))
            except Exception:
                self.main_label.setText(str(self._events[self._event_index].get('summary') or "Event"))
            self._update_nav_controls()


# ---------------------------
# Task row / Task widget
# ---------------------------
class TaskRow(QWidget):
    def __init__(self, text, done=False, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(8)

        self.label = QLabel(text)
        self.label.setWordWrap(True)
        f = self.label.font()
        ps = f.pointSize() if f.pointSize() > 0 else 10
        f.setPointSize(ps + 2)
        self.label.setFont(f)
        layout.addWidget(self.label, 1)

        btn_size = (44, 34)

        self.btn_up = QPushButton("⬆")
        self.btn_up.setFixedSize(*btn_size)
        layout.addWidget(self.btn_up)

        self.btn_down = QPushButton("⬇")
        self.btn_down.setFixedSize(*btn_size)
        layout.addWidget(self.btn_down)

        self.btn_done = QPushButton("✅")
        self.btn_done.setFixedSize(*btn_size)
        layout.addWidget(self.btn_done)

        self.btn_up.setStyleSheet("")
        self.btn_down.setStyleSheet("")
        self.btn_done.setStyleSheet("")

        self.set_done_style(done)

    def set_done_style(self, done: bool):
        f = self.label.font()
        f.setStrikeOut(done)
        self.label.setFont(f)
        if done:
            self.btn_up.setEnabled(False)
            self.btn_down.setEnabled(False)
            self.btn_done.setText("↩")
        else:
            self.btn_up.setEnabled(True)
            self.btn_down.setEnabled(True)
            self.btn_done.setText("✅")


class TaskListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self._drop_callback = None

    def set_drop_callback(self, fn):
        self._drop_callback = fn

    def dropEvent(self, event):
        super().dropEvent(event)
        if callable(self._drop_callback):
            self._drop_callback()


class TaskWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(8)

        input_layout = QHBoxLayout()
        self.task_input = QLineEdit(self)
        self.task_input.setPlaceholderText("Enter a task...")
        self.task_input.setMaxLength(MAX_TASK_LENGTH)
        self.add_button = QPushButton("Add")
        self.add_button.setFixedHeight(34)
        self.add_button.clicked.connect(self.add_task)
        input_layout.addWidget(self.task_input)
        input_layout.addWidget(self.add_button)

        self.layout.addLayout(input_layout)

        self.task_list = TaskListWidget(self)
        self.task_list.set_drop_callback(self.on_internal_move)
        self.task_list.itemDoubleClicked.connect(self.edit_task_item)
        self.layout.addWidget(self.task_list)

        self.clean_done_btn = QPushButton("Clean done tasks")
        self.clean_done_btn.clicked.connect(self.on_clean_done_clicked)
        self.clean_done_btn.setVisible(False)
        self.layout.addWidget(self.clean_done_btn)

        self.setLayout(self.layout)
        self.setGeometry(50, 350, 480, 560)

        self.tasks = []
        self._next_id = 1
        self.theme = 'Day'

        self.load_tasks()
        self.rebuild_list()
        self.update_clean_button_visibility()

    # Theme application
    def apply_theme(self, theme: str):
        """Apply theme to the task window and rows."""
        self.theme = 'Night' if str(theme).lower().startswith('n') else 'Day'

        if self.theme == 'Night':
            self.setStyleSheet(f"background-color: {DARK_BG};")
            self.task_list.setStyleSheet(
                f"QListWidget {{ background-color: {DARK_BG}; }}"
                "QListWidget::item { background-color: transparent; }"
            )
            self.add_button.setStyleSheet(PRIMARY_BTN_DARK + PRIMARY_BTN_DARK_HOVER)
            self.clean_done_btn.setStyleSheet(PRIMARY_BTN_DARK + PRIMARY_BTN_DARK_HOVER)
            self.task_input.setStyleSheet(LINEEDIT_DARK)
        else:
            self.setStyleSheet("background-color: white;")
            self.task_list.setStyleSheet(
                "QListWidget { background-color: white; }"
                "QListWidget::item { background-color: transparent; }"
            )
            self.add_button.setStyleSheet(PRIMARY_BTN_LIGHT + PRIMARY_BTN_LIGHT_HOVER)
            self.clean_done_btn.setStyleSheet(PRIMARY_BTN_LIGHT + PRIMARY_BTN_LIGHT_HOVER)
            self.task_input.setStyleSheet(LINEEDIT_LIGHT)

        self._apply_theme_to_rows()

    def _apply_theme_to_rows(self):
        """Adjust each TaskRow appearance according to theme and done state."""
        total = len(self.tasks)
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            w = self.task_list.itemWidget(item)
            if w is None:
                continue
            t = next((x for x in self.tasks if x['id'] == getattr(w, 'task_id', None)), None)
            done = bool(t.get('done', False)) if t is not None else False

            if self.theme == 'Night':
                w.label.setStyleSheet("color: white;")
                w.btn_up.setStyleSheet(ROW_BTN_DARK)
                w.btn_down.setStyleSheet(ROW_BTN_DARK)
                w.btn_done.setStyleSheet(ROW_BTN_DARK)
            else:
                if done:
                    w.label.setStyleSheet("color: gray;")
                else:
                    w.label.setStyleSheet("color: black;")
                w.btn_up.setStyleSheet(ROW_BTN_LIGHT)
                w.btn_down.setStyleSheet(ROW_BTN_LIGHT)
                w.btn_done.setStyleSheet(ROW_BTN_LIGHT)

            if total <= 1:
                w.btn_up.hide()
                w.btn_down.hide()
            else:
                w.btn_up.setVisible(True)
                w.btn_down.setVisible(True)

    # Task management
    def add_task(self):
        text = self.task_input.text().strip()
        if not text:
            return
        text = text[:MAX_TASK_LENGTH]
        task = {'id': self._next_id, 'text': text, 'done': False, 'prev_index': None}
        self._next_id += 1
        self.tasks.append(task)
        self.task_input.clear()
        self.rebuild_list()
        self.save_tasks()
        self.update_clean_button_visibility()

    def rebuild_list(self):
        """Rebuild QListWidget from self.tasks safely."""
        while self.task_list.count() > 0:
            it = self.task_list.item(0)
            w = self.task_list.itemWidget(it)
            taken = self.task_list.takeItem(0)
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            del taken

        total = len(self.tasks)

        for idx, task in enumerate(self.tasks):
            text = (task.get('text') or "")[:MAX_TASK_LENGTH]
            task['text'] = text

            item = QListWidgetItem()
            row_widget = TaskRow(text, done=bool(task.get('done', False)))
            row_widget.task_id = task['id']

            item.setSizeHint(row_widget.sizeHint())
            self.task_list.addItem(item)
            self.task_list.setItemWidget(item, row_widget)

            flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
            if (not task.get('done', False)) and total > 1:
                flags |= Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
            item.setFlags(flags)

            row_widget.btn_done.clicked.connect(partial(self.toggle_done_by_id, task['id']))
            row_widget.btn_up.clicked.connect(partial(self.move_task_by_id, task['id'], -1))
            row_widget.btn_down.clicked.connect(partial(self.move_task_by_id, task['id'], 1))

        self._apply_theme_to_rows()

    def find_index_by_id(self, task_id):
        for idx, t in enumerate(self.tasks):
            if t['id'] == task_id:
                return idx
        return -1

    def toggle_done_by_id(self, task_id):
        """Toggle done/undone: move to end when done; restore previous index when undone."""
        idx = self.find_index_by_id(task_id)
        if idx == -1:
            return

        is_done = bool(self.tasks[idx].get('done', False))
        if not is_done:
            if self.tasks[idx].get('prev_index') is None:
                self.tasks[idx]['prev_index'] = idx
            self.tasks[idx]['done'] = True
            self.tasks.append(self.tasks.pop(idx))
        else:
            prev = self.tasks[idx].get('prev_index')
            current = self.tasks.pop(idx)
            current['done'] = False
            current['prev_index'] = None
            dest = 0
            if isinstance(prev, int) and prev >= 0:
                dest = min(prev, len(self.tasks))
            self.tasks.insert(dest, current)

        self.rebuild_list()
        self.save_tasks()
        self.update_clean_button_visibility()

    def move_task_by_id(self, task_id, direction):
        """Move task up/down if possible."""
        idx = self.find_index_by_id(task_id)
        if idx == -1:
            return
        if self.tasks[idx].get('done', False):
            return
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self.tasks):
            return
        self.tasks.insert(new_idx, self.tasks.pop(idx))
        self.rebuild_list()
        self.save_tasks()

    def on_internal_move(self):
        """Rebuild the tasks list after internal drag & drop reorder in the UI."""
        new_tasks = []
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            w = self.task_list.itemWidget(item)
            if w is not None and hasattr(w, 'task_id'):
                t = next((x for x in self.tasks if x['id'] == w.task_id), None)
                if t is not None:
                    t['text'] = (w.label.text() or "")[:MAX_TASK_LENGTH]
                    new_tasks.append(t)
        self.tasks = new_tasks
        self.save_tasks()
        # rebuild to rewire signals (avoid duplicates)
        self.rebuild_list()
        self.update_clean_button_visibility()

    def edit_task_item(self, item: QListWidgetItem):
        """Edit a task on double-click; empty result removes the task."""
        w = self.task_list.itemWidget(item)
        if w is None:
            return
        current_text = w.label.text()
        new_text, ok = QInputDialog.getText(self, "Edit task", "Task:", QLineEdit.Normal, current_text)
        if ok:
            new_text = (new_text or "").strip()
            if new_text == "":
                if hasattr(w, 'task_id'):
                    self.remove_task_by_id(w.task_id)
                return
            if len(new_text) > MAX_TASK_LENGTH:
                new_text = new_text[:MAX_TASK_LENGTH]
            w.label.setText(new_text)
            if hasattr(w, 'task_id'):
                idx = self.find_index_by_id(w.task_id)
                if idx != -1:
                    self.tasks[idx]['text'] = new_text
                    self.save_tasks()

    def remove_task_by_id(self, task_id):
        idx = self.find_index_by_id(task_id)
        if idx == -1:
            return
        self.tasks.pop(idx)
        self.rebuild_list()
        self.save_tasks()
        self.update_clean_button_visibility()

    def _ask_confirm(self) -> bool:
        """Show confirmation dialog (themed) and return True if user confirmed."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirm")
        msg.setIcon(QMessageBox.Question)
        msg.setText("Are you sure you want to remove all completed tasks?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)

        if self.theme == 'Night':
            msg.setStyleSheet(QMSGBOX_DARK)
        else:
            msg.setStyleSheet(QMSGBOX_LIGHT)

        reply = msg.exec_()
        return reply == QMessageBox.Yes

    def update_clean_button_visibility(self):
        any_done = any(t.get('done', False) for t in self.tasks)
        self.clean_done_btn.setVisible(any_done)

    def on_clean_done_clicked(self):
        """Remove all tasks marked done after confirmation."""
        if self._ask_confirm():
            self.tasks = [t for t in self.tasks if not t.get('done', False)]
            for t in self.tasks:
                t['prev_index'] = None
            self.rebuild_list()
            self.save_tasks()
            self.update_clean_button_visibility()

    # Save / Load (QSettings, JSON)
    def save_tasks(self):
        settings = QSettings("MyCompany", "MyWidgetApp")
        try:
            settings.setValue("tasks", json.dumps(self.tasks, ensure_ascii=False))
        except Exception:
            # fallback: save minimal structure
            settings.setValue("tasks", json.dumps([{'text': t['text'], 'done': t.get('done', False)} for t in self.tasks], ensure_ascii=False))

    def load_tasks(self):
        settings = QSettings("MyCompany", "MyWidgetApp")
        raw = settings.value("tasks", "")
        if raw is None or raw == "":
            self.tasks = []
            return
        try:
            data = json.loads(raw)
            if isinstance(data, list) and all(isinstance(x, str) for x in data):
                self.tasks = []
                for text in data:
                    short = (text or "")[:MAX_TASK_LENGTH]
                    self.tasks.append({'id': self._next_id, 'text': short, 'done': False, 'prev_index': None})
                    self._next_id += 1
            elif isinstance(data, list) and all(isinstance(x, dict) for x in data):
                self.tasks = []
                for entry in data:
                    if 'id' in entry and isinstance(entry['id'], int):
                        tid = entry['id']
                    else:
                        tid = self._next_id
                        self._next_id += 1
                    text = (entry.get('text', '') or "")[:MAX_TASK_LENGTH]
                    done = bool(entry.get('done', False))
                    prev_index = entry.get('prev_index', None)
                    if isinstance(prev_index, int) and prev_index < 0:
                        prev_index = None
                    self.tasks.append({'id': tid, 'text': text, 'done': done, 'prev_index': prev_index})
                    if tid >= self._next_id:
                        self._next_id = tid + 1
            else:
                self.tasks = []
        except Exception:
            self.tasks = []

    def _remove_item(self, item: QListWidgetItem, widget: QWidget):
        """Deprecated compatibility helper."""
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
        """Deprecated swap helper - left for compatibility."""
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
# Clock widget
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

        self.setGeometry(100, 100, 460, 360)
        self.theme = 'Day'

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

    def apply_theme(self, theme: str):
        """Set color theme for clock labels."""
        self.theme = 'Night' if str(theme).lower().startswith('n') else 'Day'
        if self.theme == 'Night':
            color = DARK_BG
            style = f"color: {color};"
        else:
            style = "color: white;"
        self.day_label.setStyleSheet(style)
        self.date_label.setStyleSheet(style)
        self.time_label.setStyleSheet(style)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


# ---------------------------
# Settings window
# ---------------------------
class SettingsWindow(QWidget):
    def __init__(self, widget_app, task_widget, calendar_widget):
        super().__init__()
        self.widget_app = widget_app
        self.task_widget = task_widget
        self.calendar_widget = calendar_widget

        self.available_fonts = ["Arial", "Segoe UI", "Verdana", "Courier New"]

        # try to load an embedded font if present
        font_path = resource_path("fonts/Anurati-Regular.otf")
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

        layout.addWidget(QLabel("Calendar .ics URL:"))
        self.ics_url_edit = QLineEdit(self)
        self.ics_url_edit.setPlaceholderText("https://.../calendar.ics")
        layout.addWidget(self.ics_url_edit)

        # font selectors
        self.font_selector_day = QComboBox(self)
        self.font_selector_day.addItems(self.available_fonts)
        layout.addWidget(self.font_selector_day)

        self.font_selector_date = QComboBox(self)
        self.font_selector_date.addItems(self.available_fonts)
        layout.addWidget(self.font_selector_date)

        self.font_selector_time = QComboBox(self)
        self.font_selector_time.addItems(self.available_fonts)
        layout.addWidget(self.font_selector_time)

        # size selectors
        self.size_selector_day = QSpinBox(self)
        self.size_selector_day.setRange(4, 96)
        layout.addWidget(self.size_selector_day)

        self.size_selector_date = QSpinBox(self)
        self.size_selector_date.setRange(4, 96)
        layout.addWidget(self.size_selector_date)

        self.size_selector_time = QSpinBox(self)
        self.size_selector_time.setRange(4, 96)
        layout.addWidget(self.size_selector_time)

        # position and offsets
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

        # theme selectors
        layout.addWidget(QLabel("Clock theme:"))
        self.theme_selector_widget = QComboBox(self)
        self.theme_selector_widget.addItems(["Day", "Night"])
        layout.addWidget(self.theme_selector_widget)

        layout.addWidget(QLabel("Tasks window theme:"))
        self.theme_selector_tasks = QComboBox(self)
        self.theme_selector_tasks.addItems(["Day", "Night"])
        layout.addWidget(self.theme_selector_tasks)

        # startup flags
        self.startup_checkbox_settings = QCheckBox("Show settings at startup")
        layout.addWidget(self.startup_checkbox_settings)
        self.startup_checkbox_settings.toggled.connect(lambda v: self._save_flag("show_settings_on_start", v))

        self.startup_checkbox_tasks = QCheckBox("Show task window at startup")
        layout.addWidget(self.startup_checkbox_tasks)
        self.startup_checkbox_tasks.toggled.connect(lambda v: self._save_flag("show_tasks_on_start", v))

        self.startup_checkbox_widget = QCheckBox("Show time widget at startup")
        layout.addWidget(self.startup_checkbox_widget)
        self.startup_checkbox_widget.toggled.connect(lambda v: self._save_flag("show_widget_on_start", v))
        self.startup_checkbox_calendar = QCheckBox("Show calendar at startup")
        layout.addWidget(self.startup_checkbox_calendar)
        self.startup_checkbox_calendar.toggled.connect(lambda v: self._save_flag("show_calendar_on_start", v))

        # actions
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
        self.setGeometry(1350, 250, 520, 560)

    def _save_flag(self, key: str, checked: bool):
        settings = QSettings("MyCompany", "MyWidgetApp")
        settings.setValue(key, bool(checked))

    def apply_clicked(self):
        # save calendar URL
        settings = QSettings("MyCompany", "MyWidgetApp")
        settings.setValue("calendar_url", self.ics_url_edit.text().strip())

        # fonts / sizes / position
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

        chosen_theme_widget = self.theme_selector_widget.currentText()
        chosen_theme_tasks = self.theme_selector_tasks.currentText()
        self.widget_app.apply_theme(chosen_theme_widget)
        self.task_widget.apply_theme(chosen_theme_tasks)

        self.widget_app.update_time()
        self.save_settings()

        # trigger calendar update immediately
        try:
            self.calendar_widget.update_event()
        except Exception:
            pass

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

        settings.setValue("theme_widget", str(self.theme_selector_widget.currentText()))
        settings.setValue("theme_tasks", str(self.theme_selector_tasks.currentText()))

        settings.setValue("show_settings_on_start", bool(self.startup_checkbox_settings.isChecked()))
        settings.setValue("show_tasks_on_start", bool(self.startup_checkbox_tasks.isChecked()))
        settings.setValue("show_widget_on_start", bool(self.startup_checkbox_widget.isChecked()))
        settings.setValue("show_calendar_on_start", bool(self.startup_checkbox_calendar.isChecked()))

    def load_settings(self):
        settings = QSettings("MyCompany", "MyWidgetApp")

        self.ics_url_edit.setText(settings.value("calendar_url", "", type=str))

        self.font_selector_day.setCurrentText(settings.value("fonts/day", self.available_fonts[0]))
        self.font_selector_date.setCurrentText(settings.value("fonts/date", "Verdana"))
        self.font_selector_time.setCurrentText(settings.value("fonts/time", "Verdana"))

        self.size_selector_day.setValue(int(settings.value("sizes/day", 40)))
        self.size_selector_date.setValue(int(settings.value("sizes/date", 21)))
        self.size_selector_time.setValue(int(settings.value("sizes/time", 15)))

        self.position_selector.setCurrentText(settings.value("position", "Top-center"))
        self.offset_x_spin.setValue(int(settings.value("offset_x", 0)))
        self.offset_y_spin.setValue(int(settings.value("offset_y", 50)))

        theme_widget = settings.value("theme_widget", "Day")
        if theme_widget not in ("Day", "Night"):
            theme_widget = "Day"
        self.theme_selector_widget.setCurrentText(theme_widget)

        theme_tasks = settings.value("theme_tasks", "Day")
        if theme_tasks not in ("Day", "Night"):
            theme_tasks = "Day"
        self.theme_selector_tasks.setCurrentText(theme_tasks)

        show_settings = settings.value("show_settings_on_start", True, type=bool)
        show_tasks = settings.value("show_tasks_on_start", True, type=bool)
        show_widget = settings.value("show_widget_on_start", True, type=bool)
        show_calendar = settings.value("show_calendar_on_start", True, type=bool)

        self.startup_checkbox_settings.setChecked(bool(show_settings))
        self.startup_checkbox_tasks.setChecked(bool(show_tasks))
        self.startup_checkbox_widget.setChecked(bool(show_widget))
        self.startup_checkbox_calendar.setChecked(bool(show_calendar))

    def finish_clicked(self):
        self.hide()


def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)


def main():
    app = QApplication(sys.argv)
    widget_app = WidgetApp()
    task_widget = TaskWidget()
    calendar_widget = CalendarWidget()
    settings_window = SettingsWindow(widget_app, task_widget, calendar_widget)

    tray_icon = QSystemTrayIcon()
    tray_icon.setIcon(QIcon(resource_path("icon/Logo.ico")))
    tray_icon.setVisible(True)

    tray_menu = QMenu()
    tray_menu.addAction("Show Clock", widget_app.show)
    tray_menu.addAction("Hide Clock", widget_app.hide)
    tray_menu.addAction("Show Tasks", task_widget.show)
    tray_menu.addAction("Hide Tasks", task_widget.hide)
    tray_menu.addAction("Show Calendar", calendar_widget.show)
    tray_menu.addAction("Hide Calendar", calendar_widget.hide)
    tray_menu.addAction("Settings", settings_window.show)
    tray_menu.addAction("Exit", app.quit)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.activated.connect(
        lambda reason: widget_app.show() if reason == QSystemTrayIcon.DoubleClick else None
    )

    widget_app.update_time()
    calendar_widget.update_event()

    settings = QSettings("MyCompany", "MyWidgetApp")
    if settings.value("show_widget_on_start", True, type=bool):
        widget_app.show()
    if settings.value("show_tasks_on_start", True, type=bool):
        task_widget.show()
    if settings.value("show_calendar_on_start", True, type=bool):
        calendar_widget.show()
    if settings.value("show_settings_on_start", True, type=bool):
        settings_window.show()

    def post_launch_apply():
        settings_window.apply_clicked()
        widget_app.update_time()
        calendar_widget.update_event()

    QTimer.singleShot(300, post_launch_apply)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
