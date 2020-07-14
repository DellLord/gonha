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
from pathlib import Path

app = QtWidgets.QApplication(sys.argv)
resource_path = os.path.dirname(__file__)
cfgFile = f'{Path.home()}/.config/gonha/config.ini'
iface = 'enp5s0'


class ThreadNetworkStats(QtCore.QThread):
    signal = QtCore.pyqtSignal(dict, name='ThreadNetworkFinish')

    def __init__(self, parent=None):
        super(ThreadNetworkStats, self).__init__(parent)
        self.finished.connect(self.threadFinished)

    def threadFinished(self):
        self.start()

    def run(self):
        counter1 = psutil.net_io_counters(pernic=True)[iface]
        time.sleep(1)
        counter2 = psutil.net_io_counters(pernic=True)[iface]
        downSpeed = f'{humanfriendly.format_size(counter2.bytes_recv - counter1.bytes_recv)}/s'

        upSpeed = f'{humanfriendly.format_size(counter2.bytes_sent - counter1.bytes_sent)}/s'
        self.signal.emit({'downSpeed': downSpeed, 'upSpeed': upSpeed})


class ThreadSlow(QtCore.QThread):
    signal = QtCore.pyqtSignal(dict, name='ThreadSlowFinish')

    def __init__(self, parent=None):
        super(ThreadSlow, self).__init__(parent)
        self.finished.connect(self.threadFinished)

    def threadFinished(self):
        self.start()

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
        time.sleep(10)
        self.signal.emit(self.getPartitions())


class ThreadFast(QtCore.QThread):
    signal = QtCore.pyqtSignal(dict, name='ThreadFastFinish')
    message = dict()

    def __init__(self, parent=None):
        super(ThreadFast, self).__init__(parent)
        self.finished.connect(self.threadFinished)

    def threadFinished(self):
        # print('Thread Fast Finished')
        self.start()

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
    threadNetworkStats = ThreadNetworkStats()
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
        self.ifaceValueLabel = self.findChild(QtWidgets.QLabel, 'ifaceValueLabel')
        self.downloadValueLabel = self.findChild(QtWidgets.QLabel, 'downloadValueLabel')
        self.uploadValueLabel = self.findChild(QtWidgets.QLabel, 'uploadValueLabel')
        # -------------------------------------------------------------
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        # Connect Threads Signals
        self.threadFast.signal.connect(self.receiveThreadFastfinish)
        self.threadSlow.signal.connect(self.receiveThreadSlowFinish)
        self.threadNetworkStats.signal.connect(self.receiveThreadNetworkStats)
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
        self.threadSlow.start()
        self.threadNetworkStats.start()
        # ----------------------------------
        # verify if config file exists
        # in $HOME/.config/gonha
        self.startConfig()
        # ----------------------------------
        self.loadConfigs()
        self.displayPartitions()

    @staticmethod
    def startConfig():
        # verify if config file exists
        if not (os.path.isfile(cfgFile)):
            if not (os.path.isdir(f'{Path.home()}/.config/gonha')):
                os.makedirs(f'{Path.home()}/.config/gonha')

            file = open(cfgFile, 'w')
            lines = [
                "[DEFAULT]\n",
                "position = topRight\n"
            ]
            file.writelines(lines)
            file.close()

    def receiveThreadNetworkStats(self, message):
        # print(message)
        self.ifaceValueLabel.setText(iface)
        self.downloadValueLabel.setText(message['downSpeed'])
        self.uploadValueLabel.setText(message['upSpeed'])

    def displayPartitions(self):
        mntPoints = self.threadSlow.getPartitions()
        font = QtGui.QFont('Fira Code', 11)
        orange = 'color: rgb(252, 126, 0);'
        white = 'color: rgb(255, 255, 255);'
        for i, mntPoint in enumerate(mntPoints['partitions']):
            horizontalLayout = QtWidgets.QHBoxLayout()

            mountpointValueLabel = QtWidgets.QLabel(f"{mntPoint['mountpoint']}")
            mountpointValueLabel.setFont(font)
            mountpointValueLabel.setStyleSheet(white)
            horizontalLayout.addWidget(mountpointValueLabel)

            usedLabel = QtWidgets.QLabel(f"used:")
            usedLabel.setStyleSheet(orange)
            usedLabel.setFont(font)
            usedLabel.setStyleSheet('color: rgb(252, 126, 0);')
            horizontalLayout.addWidget(usedLabel)

            usedValueLabel = QtWidgets.QLabel(f"{mntPoint['used']}")
            usedValueLabel.setFont(font)
            usedValueLabel.setStyleSheet(white)
            horizontalLayout.addWidget(usedValueLabel)

            totalLabel = QtWidgets.QLabel(f"total: ")
            totalLabel.setStyleSheet(orange)
            horizontalLayout.addWidget(totalLabel)

            totalValueLabel = QtWidgets.QLabel(f"{mntPoint['total']}")
            totalValueLabel.setFont(font)
            totalValueLabel.setStyleSheet(white)
            horizontalLayout.addWidget(totalValueLabel)

            percentLabel = QtWidgets.QLabel(f"percent:")
            percentLabel.setStyleSheet(orange)
            percentLabel.setFont(font)
            horizontalLayout.addWidget(percentLabel)

            percentValueLabel = QtWidgets.QLabel(f"{mntPoint['percent']}")
            percentValueLabel.setFont(font)
            percentValueLabel.setStyleSheet(white)
            horizontalLayout.addWidget(percentValueLabel)

            self.partitionsLabels.append(
                {
                    'mountpointValueLabel': mountpointValueLabel,
                    'usedValueLabel': usedValueLabel,
                    'totalValueLabel': totalValueLabel,
                    'percentValueLabel': percentValueLabel
                }
            )

            # print(self.partitionsLabels)

            self.fsVerticalLayout.addLayout(horizontalLayout)

    def loadConfigs(self):
        config = configparser.ConfigParser()
        config.read(cfgFile)
        # print(config['DEFAULT']['position'])
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
        for i, label in enumerate(self.partitionsLabels):
            label['mountpointValueLabel'].setText(message['partitions'][i]['mountpoint'])
            label['usedValueLabel'].setText(message['partitions'][i]['used'])
            label['totalValueLabel'].setText(message['partitions'][i]['total'])
            label['percentValueLabel'].setText(message['partitions'][i]['percent'])

    def receiveThreadFastfinish(self, message):
        self.hourLabel.setText(message['hourLabel'])
        self.minuteLabel.setText(message['minuteLabel'])
        self.ampmLabel.setText(message['ampmLabel'])
        self.dateLabel.setText(message['dateLabel'])
        self.memValueLabel.setText(message['memValueLabel'])
        self.cpuValueLabel.setText(message['cpuValueLabel'])
        self.temperatureValueLabel.setText(message['temperatureValueLabel'])

