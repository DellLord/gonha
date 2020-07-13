import os
import sys
from PyQt5 import QtWidgets, uic, QtCore, QtGui
from ewmh import EWMH
import time
from datetime import datetime
import psutil
import configparser
import lsb_release
import humanfriendly

app = QtWidgets.QApplication(sys.argv)
resource_path = os.path.join(os.path.split(__file__)[0], './')
cfgFile = f'{resource_path}/config.ini'


class ThreadSlow(QtCore.QThread):
    signal = QtCore.pyqtSignal(dict, name='ThreadSlowFinish')

    def __init__(self, parent=None):
        super(ThreadSlow, self).__init__(parent)

    @staticmethod
    def getPartitions():
        msg = dict()
        partitions = psutil.disk_partitions()
        msg['partitions'] = []
        for partition in partitions:
            if (not ('boot' in partition.mountpoint)) and (not ('snap' in partition.mountpoint)):
                disk_usage = psutil.disk_usage(partition.mountpoint)
                msg['partitions'].append(
                    {
                        'mountpoint': partition.mountpoint,
                        'total': humanfriendly.format_size(disk_usage.total),
                        'used': humanfriendly.format_size(disk_usage.used),
                        'free': humanfriendly.format_size(disk_usage.free),
                        'percent': f'{disk_usage.percent}%'
                    }
                )

        return msg

    def run(self):
        pass


class ThreadFast(QtCore.QThread):
    signal = QtCore.pyqtSignal(dict, name='ThreadFastFinish')
    message = dict()

    def __init__(self, parent=None):
        super(ThreadFast, self).__init__(parent)

    def run(self):
        now = datetime.now()
        self.message['hourLabel'] = now.strftime('%I')
        self.message['minuteLabel'] = now.strftime('%M')
        self.message['secondsLabel'] = now.strftime('%S')
        self.message['dateLabel'] = now.strftime("%A, %d %B %Y")
        self.message['ampmLabel'] = now.strftime('%p')
        self.message['cpuValueLabel'] = f"{psutil.cpu_percent()}%"
        self.message['memValueLabel'] = f"{psutil.virtual_memory().percent}%"
        sensors = psutil.sensors_temperatures()
        for key in sensors:
            self.message['temperatureValueLabel'] = f'{int(sensors[key][0].current)}°'
            break

        time.sleep(2)
        self.signal.emit(self.message)


class MainWindow(QtWidgets.QMainWindow):
    threadFast = ThreadFast()
    threadSlow = ThreadSlow()
    partitionsLabels = []

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi(f'{resource_path}/mainwindow.ui', self)
        flags = QtCore.Qt.FramelessWindowHint
        flags |= QtCore.Qt.WindowStaysOnBottomHint
        flags |= QtCore.Qt.Tool
        # -------------------------------------------------------------
        # Find Childs
        self.hourLabel = self.findChild(QtWidgets.QLabel, 'hourLabel')
        self.minuteLabel = self.findChild(QtWidgets.QLabel, 'minuteLabel')
        self.ampmLabel = self.findChild(QtWidgets.QLabel, 'ampmLabel')
        self.dateLabel = self.findChild(QtWidgets.QLabel, 'dateLabel')
        self.memValueLabel = self.findChild(QtWidgets.QLabel, 'memValueLabel')
        self.cpuValueLabel = self.findChild(QtWidgets.QLabel, 'cpuValueLabel')
        self.lsbreleaseLabel = self.findChild(QtWidgets.QLabel, 'lsbreleaseLabel')
        self.temperatureValueLabel = self.findChild(QtWidgets.QLabel, 'temperatureValueLabel')
        self.fsVerticalLayout = self.findChild(QtWidgets.QVBoxLayout, 'fsVerticalLayout')
        # -------------------------------------------------------------
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        # Connect Thread Signal
        self.threadFast.signal.connect(self.receiveThreadFastfinish)
        self.moveTopRight()
        self.show()
        # Show in all workspaces
        ew = EWMH()
        all_wins = ew.getClientList()
        wins = filter(lambda w: w.get_wm_class()[1] == 'gonha', all_wins)
        for w in wins:
            print(w)
            ew.setWmDesktop(w, 0xffffffff)

        ew.display.flush()
        self.threadFast.start()
        self.loadConfigs()
        self.displayPartitions()

    def displayPartitions(self):
        mntPoints = self.threadSlow.getPartitions()
        font = QtGui.QFont('Fira Code', 11)
        styleSheet = 'color: rgb(252, 126, 0);'
        for i, mntPoint in enumerate(mntPoints['partitions']):
            horizontalLayout = QtWidgets.QHBoxLayout()

            mountpointValueLabel = QtWidgets.QLabel(f"{mntPoint['mountpoint']}")
            mountpointValueLabel.setFont(font)
            horizontalLayout.addWidget(mountpointValueLabel)
            self.partitionsLabels.append(mountpointValueLabel)

            usedLabel = QtWidgets.QLabel(f"used:")
            usedLabel.setStyleSheet(styleSheet)
            usedLabel.setFont(font)
            horizontalLayout.addWidget(usedLabel)
            self.partitionsLabels.append(usedLabel)

            usedValueLabel = QtWidgets.QLabel(f"{mntPoint['used']}")
            usedValueLabel.setFont(font)
            horizontalLayout.addWidget(usedValueLabel)
            self.partitionsLabels.append(usedValueLabel)

            totalLabel = QtWidgets.QLabel(f"total: ")
            totalLabel.setStyleSheet(styleSheet)
            horizontalLayout.addWidget(totalLabel)
            self.partitionsLabels.append(totalLabel)

            totalValueLabel = QtWidgets.QLabel(f"{mntPoint['total']}")
            totalValueLabel.setFont(font)
            horizontalLayout.addWidget(totalValueLabel)
            self.partitionsLabels.append(totalValueLabel)

            percentLabel = QtWidgets.QLabel(f"percent:")
            percentLabel.setStyleSheet(styleSheet)
            percentLabel.setFont(font)
            horizontalLayout.addWidget(percentLabel)
            self.partitionsLabels.append(percentLabel)

            percentValueLabel = QtWidgets.QLabel(f"{mntPoint['percent']}")
            percentValueLabel.setFont(font)
            horizontalLayout.addWidget(percentValueLabel)
            self.partitionsLabels.append(percentValueLabel)

            self.fsVerticalLayout.addLayout(horizontalLayout)

    def loadConfigs(self):
        config = configparser.ConfigParser()
        config.read(cfgFile)
        print(config['DEFAULT']['position'])
        if config['DEFAULT']['position'] == 'topLeft':
            self.moveTopLeft()
        else:
            self.moveTopRight()

        distroInfo = lsb_release.get_distro_information()
        self.lsbreleaseLabel.setText(
            f"{distroInfo['DESCRIPTION']} codename {distroInfo['CODENAME']}")

    @staticmethod
    def writeConfig(cfg):
        config = configparser.ConfigParser()
        config['DEFAULT'] = cfg
        with open(cfgFile, 'w') as configfile:
            config.write(configfile)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        contextMenu = QtWidgets.QMenu(self)
        topLeftAction = contextMenu.addAction('Top Left')
        topRightAction = contextMenu.addAction('Top Right')
        aboutAction = contextMenu.addAction('A&bout')
        quitAction = contextMenu.addAction('&Quit')
        action = contextMenu.exec_(self.mapToGlobal(event.pos()))
        if action == topLeftAction:
            self.writeConfig({'position': 'topLeft'})
            self.moveTopLeft()
        elif action == topRightAction:
            self.writeConfig({'position': 'topRight'})
            self.moveTopRight()
        elif action == quitAction:
            sys.exit()

    def moveTopLeft(self):
        self.move(0, 10)

    def moveTopRight(self):
        screen = app.primaryScreen()
        print('Screen: %s' % screen.name())
        size = screen.size()
        print('Size: %d x %d' % (size.width(), size.height()))
        rect = screen.availableGeometry()
        print('Available: %d x %d' % (rect.width(), rect.height()))
        # move window to top right
        win = self.geometry()
        print(f'mainwindow size {win.width()} x {win.height()}')
        self.move(rect.width() - win.width(), 0)

    def receiveThreadSlowFinish(self, message):
        print('Receiving msg of the threadslow', message)

    def receiveThreadFastfinish(self, message):
        self.hourLabel.setText(message['hourLabel'])
        self.minuteLabel.setText(message['minuteLabel'])
        self.ampmLabel.setText(message['ampmLabel'])
        self.dateLabel.setText(message['dateLabel'])
        self.memValueLabel.setText(message['memValueLabel'])
        self.cpuValueLabel.setText(message['cpuValueLabel'])
        self.temperatureValueLabel.setText(message['temperatureValueLabel'])
        self.threadFast.start()
