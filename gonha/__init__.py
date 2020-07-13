import os
import sys
from PyQt5 import QtWidgets, uic, QtCore, QtGui
from ewmh import EWMH
import time
from datetime import datetime
import psutil

app = QtWidgets.QApplication(sys.argv)
resource_path = os.path.join(os.path.split(__file__)[0], './')


class ThreadClass(QtCore.QThread):
    signal = QtCore.pyqtSignal(dict, name='ThreadFinish')

    def __init__(self, parent=None):
        super(ThreadClass, self).__init__(parent)

    def run(self):
        message = dict()
        now = datetime.now()
        message['hourLabel'] = now.strftime('%I')
        message['minuteLabel'] = now.strftime('%M')
        message['secondsLabel'] = now.strftime('%S')
        message['dateLabel'] = now.strftime("%A, %d %B %Y")
        message['ampmLabel'] = now.strftime('%p')
        message['hddValueLabel'] = f"{psutil.disk_usage('/').percent}%"
        message['cpuValueLabel'] = f"{psutil.cpu_percent()}%"
        message['memValueLabel'] = f"{psutil.virtual_memory().percent}%"
        time.sleep(2)
        self.signal.emit(message)


class MainWindow(QtWidgets.QMainWindow):
    thread = ThreadClass()

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi(f'{resource_path}./mainwindow.ui', self)
        flags = QtCore.Qt.FramelessWindowHint
        flags |= QtCore.Qt.WindowStaysOnBottomHint
        flags |= QtCore.Qt.Tool
        # -------------------------------------------------------------
        # Find Childs
        self.hourLabel = self.findChild(QtWidgets.QLabel, 'hourLabel')
        self.minuteLabel = self.findChild(QtWidgets.QLabel, 'minuteLabel')
        self.ampmLabel = self.findChild(QtWidgets.QLabel, 'ampmLabel')
        self.dateLabel = self.findChild(QtWidgets.QLabel, 'dateLabel')
        self.hddValueLabel = self.findChild(QtWidgets.QLabel, 'hddValueLabel')
        self.memValueLabel = self.findChild(QtWidgets.QLabel, 'memValueLabel')
        self.cpuValueLabel = self.findChild(QtWidgets.QLabel, 'cpuValueLabel')
        # -------------------------------------------------------------
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        # Connect Thread Signal
        self.thread.signal.connect(self.receiveThreadfinish)
        # self.move(2400, 0)
        self.topRight()
        self.show()
        # Show in all workspaces
        ew = EWMH()
        all_wins = ew.getClientList()
        wins = filter(lambda w: w.get_wm_class()[1] == 'gonha', all_wins)
        for w in wins:
            print(w)
            ew.setWmDesktop(w, 0xffffffff)

        ew.display.flush()
        self.thread.start()

    def topRight(self):
        screen = app.primaryScreen()
        print('Screen: %s' % screen.name())
        size = screen.size()
        print('Size: %d x %d' % (size.width(), size.height()))
        rect = screen.availableGeometry()
        print('Available: %d x %d' % (rect.width(), rect.height()))
        # move window to top right
        win = self.geometry()
        print(f'mainwindow size {win.width()} x {win.height()}')
        self.move((rect.width() - 10) - win.width(), 0)

    def receiveThreadfinish(self, message):
        self.hourLabel.setText(message['hourLabel'])
        self.minuteLabel.setText(message['minuteLabel'])
        self.ampmLabel.setText(message['ampmLabel'])
        self.dateLabel.setText(message['dateLabel'])
        self.hddValueLabel.setText(message['hddValueLabel'])
        self.memValueLabel.setText(message['memValueLabel'])
        self.cpuValueLabel.setText(message['cpuValueLabel'])
        print(message)
        self.thread.start()
