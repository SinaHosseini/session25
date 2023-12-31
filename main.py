import sys
import time
from functools import partial
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtUiTools import QUiLoader
from mytime import MyTime
from thread_stopwatch import StopWatchThread
from thread_timer import TimerThread
from thread_worldclock import WorldClockThread
from thread_alarm import AlarmThread
from main_window import Ui_MainWindow
from plyer.utils import platform
from plyer import notification
import qdarktheme
from database import Database
from fontTools.ttLib import TTFont


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.label_stopwatch.setText("0:0:0")
        self.ui.btn_start_stopwatch.clicked.connect(self.start_stopwatch)
        self.ui.btn_stop_timer.clicked.connect(self.stop_stopwatch)
        self.ui.btn_reset_stopwatch.clicked.connect(self.reset_stopwatch)
        self.ui.btn_start_timer.clicked.connect(self.start_timer)
        self.ui.btn_stop_timer.clicked.connect(self.stop_timer)
        self.ui.btn_reset_timer.clicked.connect(self.reset_timer)
        self.ui.btn_add_alarm.clicked.connect(self.add_alarm)
        id = QFontDatabase.addApplicationFont("Seven Segment.ttf")
        families = QFontDatabase.applicationFontFamilies(id)
        self.ui.label_stopwatch.setFont(QFont(families[0], 40))
        self.ui.tb_hour_timer.setFont(QFont(families[0], 40))
        self.ui.tb_minute_timer.setFont(QFont(families[0], 40))
        self.ui.tb_second_timer.setFont(QFont(families[0], 40))
        qdarktheme.setup_theme("dark")

        self.alarm_lb = []
        self.alarm_edits = []
        self.editable = True

        self.db = Database()
        self.thread_stopwatch = StopWatchThread()
        self.thread_timer = TimerThread()
        self.thread_world_clock = WorldClockThread()
        self.thread_alarm = AlarmThread()
        self.read_from_database()
        self.thread_stopwatch.signal_show.connect(self.show_number_stopwatch)
        self.thread_timer.signal_show.connect(self.show_time_timer)
        self.thread_world_clock.signal_show.connect(self.show_world_clock)
        self.thread_world_clock.start()

    def close_event(self, event):
        self.thread_world_clock.terminate()
        self.thread_alarm.terminate()
        self.thread_stopwatch.terminate()
        self.thread_timer.terminate()
        event.accept()

    def read_from_database(self):
        alarm = self.db.get_alarms()
        self.alarm_lb = []
        for row in range(len(alarm)):
            self.add_alarm_to_grid(alarm, row)

    def add_alarm(self):
        if not self.editable:
            self.editable = True
            self.ui.btn_add_alarm.setText("Add")
            self.ui.time_edit.setStyleSheet("")
            self.thread_alarm.Time_Alarms[self.edit_alarm_row] = MyTime(self.ui.time_edit.time(
            ).hour(), self.ui.time_edit.time().minute(), self.ui.time_edit.time().second())
            self.db.edit_alarm(
                self.thread_alarm.Time_Alarms[self.edit_alarm_row].convert_time_to_second(), self.edit_alarm_id)
        else:
            self.db.add_new_alarm(MyTime.convert_time_to_second(MyTime(self.ui.time_edit.time(
            ).hour(), self.ui.time_edit.time().minute(), self.ui.time_edit.time().second())))
        self.remove_alarm()
        self.read_from_database()

    def add_alarm_to_grid(self, alarm, row):
        new_label = QLabel()
        new_btn = QPushButton()
        new_btn_edit = QPushButton()
        new_time = MyTime.convert_second_to_time(alarm[row][1])
        self.thread_alarm.Time_Alarms.append(new_time)
        new_label.setText(
            f"{new_time.hour}:{new_time.minute}:{new_time.second}")
        new_label.setFont(QFont("Centaur", pointSize=15))
        new_btn_edit.setText("📝")
        new_btn.setText("❌")
        new_btn.setMaximumWidth(50)
        new_btn_edit.setMaximumWidth(50)
        self.alarm_lb.append(new_label)
        self.alarm_edits.append(new_btn_edit)

        self.ui.gl_alarms.addWidget(new_label, row, 0)
        self.ui.gl_alarms.addWidget(new_btn_edit, row, 1)
        self.ui.gl_alarms.addWidget(new_btn, row, 2)

        new_btn_edit.clicked.connect(
            partial(self.edit_alarm, row, alarm[row][0]))
        new_btn.clicked.connect(partial(self.remove_alarm, alarm[row][0]))

    def edit_alarm(self, row, id):
        if self.editable:
            self.editable = False
        else:
            return

        self.ui.btn_add_alarm.setText("Save")
        self.ui.time_edit.setStyleSheet(
            "background-color: yellow; color: black;")
        self.alarm_lb[row].setStyleSheet(
            "background-color: yellow; color: black;")
        self.thread_alarm.Time_Alarms[row] = MyTime(
            self.thread_alarm.Time_Alarms[row].hour, self.thread_alarm.Time_Alarms[row].minute, self.thread_alarm.Time_Alarms[row].second)
        self.ui.time_edit.setTime(QTime(
            self.thread_alarm.Time_Alarms[row].hour, self.thread_alarm.Time_Alarms[row].minute, self.thread_alarm.Time_Alarms[row].second))
        self.edit_alarm_id = id
        self.edit_alarm_row = row

    def remove_alarm(self, id=None):
        if id != None:
            self.db.remove_alarm(id)
            children = []
            for i in range(self.ui.gl_alarms.count()):
                child = self.ui.gl_alarms.itemAt(i).widget()
                if child:
                    children.append(child)
            for child in children:
                child.deleteLater()
            self.read_from_database()

    def show_world_clock(self):
        self.thread_world_clock.timeBerlin = self.thread_world_clock.timeTehran.sub(
            MyTime(2, 30, 0))
        self.thread_world_clock.timeWashington = self.thread_world_clock.timeTehran.sub(
            MyTime(7, 30, 0))
        self.ui.lb_tehran.setText(
            f"{self.thread_world_clock.timeTehran.hour}:{self.thread_world_clock.timeTehran.minute}:{self.thread_world_clock.timeTehran.second}")
        self.ui.lb_berlin.setText(
            f"{self.thread_world_clock.timeBerlin.hour}:{self.thread_world_clock.timeBerlin.minute}:{self.thread_world_clock.timeBerlin.second}")
        self.ui.lb_washington.setText(
            f"{self.thread_world_clock.timeWashington.hour}:{self.thread_world_clock.timeWashington.minute}:{self.thread_world_clock.timeWashington.second}")

    # @Slot
    def start_stopwatch(self):
        self.thread_stopwatch.start()

    def show_number_stopwatch(self):
        self.ui.label_stopwatch.setText(
            f"{self.thread_stopwatch.time.hour}:{self.thread_stopwatch.time.minute}:{self.thread_stopwatch.time.second}")

    def reset_stopwatch(self):
        self.thread_stopwatch.reset()

    def stop_stopwatch(self):
        self.thread_stopwatch.terminate()

    def start_timer(self):
        if self.thread_timer.time.second + self.thread_timer.time.minute + self.thread_timer.time.hour != 0:
            self.thread_timer.set_time(int(self.ui.tb_hour_timer.text()), int(
                self.ui.tb_minute_timer.text()), int(self.ui.tb_second_timer.text()))
            self.thread_timer.start()

    def show_time_timer(self):
        self.ui.tb_hour_timer.setText(str(self.thread_timer.time.hour))
        self.ui.tb_minute_timer.setText(str(self.thread_timer.time.minute))
        self.ui.tb_second_timer.setText(str(self.thread_timer.time.second))
        if self.thread_timer.time.second + self.thread_timer.time.minute + self.thread_timer.time.hour == 0:
            self.thread_timer.terminate()
            notification.notify(
                title='Clock', message='Timer Alarm', app_name='Clock')

    def stop_timer(self):
        self.thread_timer.terminate()

    def reset_timer(self):
        self.thread_timer.set_time(0, 15, 0)
        self.ui.tb_hour_timer.setText(str(self.thread_timer.time.hour))
        self.ui.tb_minute_timer.setText(str(self.thread_timer.time.minute))
        self.ui.tb_second_timer.setText(str(self.thread_timer.time.second))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    app.exec()
