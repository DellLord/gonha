import os
import sys
from PyQt5 import QtWidgets, uic, QtCore, QtGui
from ewmh import EWMH
import time
from datetime import datetime
import psutil
import humanfriendly
from pathlib import Path
import pkg_resources
from colr import color
from PyInquirer import prompt, print_json
import re
import json
from configobj import ConfigObj

app = QtWidgets.QApplication(sys.argv)
resource_path = os.path.dirname(__file__)


class Config:

    def __init__(self):
        # Config file
        self.cfgFile = f'{Path.home()}/.config/gonha/config.json'
        self.globalJSON = dict()
        self.aboutdialogFile = pkg_resources.resource_filename('gonha', 'aboutdialog.ui')
        self.version = self.getVersion()
        if not os.path.isfile(self.cfgFile):
            print(color('Config file not found in : ', fore=9), color(f'{self.cfgFile}', fore=11))
            print(color('Starting Wizard...', fore=14))
            print('')

            # Position Question
            positionQuestions = [
                {
                    'type': 'list',
                    'name': 'position',
                    'message': 'What position do you want on the screen?',
                    'choices': [
                        'Top Left',
                        'Top Right',
                    ],
                }
            ]
            positionResponse = prompt(positionQuestions)
            self.updateConfig(positionResponse)

            # Date Format Question
            dateFormatQuestions = [
                {
                    'type': 'list',
                    'name': 'dateFormat',
                    'message': 'Select time format',
                    'choices': [
                        '12 hours',
                        '24 hours',
                    ]
                }
            ]
            dateFormatResponse = prompt(dateFormatQuestions)
            self.updateConfig(dateFormatResponse)

            # Temperature Question
            sensors = psutil.sensors_temperatures()
            tempUserChoices = []
            for i, key in enumerate(sensors):
                tempUserChoices.append(
                    '{} - [{}] current temp: {:.2f}°'.format(i, key, float(sensors[key][i].current))
                )

            # Temperature Questions
            tempQuestions = [
                {
                    'type': 'list',
                    'name': 'temp',
                    'message': 'Select what is temperature sensor you want gonha to show',
                    'choices': tempUserChoices,
                    'filter': lambda val: tempUserChoices.index(val)
                }
            ]
            tempResponse = prompt(tempQuestions)
            self.updateConfig(tempResponse)

            partitionsChoices = []
            # Filesystem sections
            for partition in psutil.disk_partitions():
                partitionsChoices.append(
                    {
                        'name': 'device: [{}] mountpoint: [{}] fstype: {}'.format(partition.device,
                                                                                  partition.mountpoint,
                                                                                  partition.fstype),
                        'value': partition.mountpoint
                    }
                )

            partitionQuestions = [
                {
                    'type': 'checkbox',
                    'name': 'filesystems',
                    'message': 'Select which partitions you want to display',
                    'choices': partitionsChoices,
                }
            ]
            partitionsResponse = prompt(partitionQuestions)
            self.updateConfig(partitionsResponse)

            # Interface Name
            ifaceChoices = []
            for net_if_addr in psutil.net_if_addrs():
                ifaceChoices.append('{}'.format(net_if_addr))

            ifaceQuestions = [
                {
                    'type': 'list',
                    'name': 'iface',
                    'message': 'Select the network interface to donwload e upload rate stats.',
                    'choices': ifaceChoices
                }
            ]
            ifaceResponse = prompt(ifaceQuestions)
            self.updateConfig(ifaceResponse)

            # Write json global
            # print(self.globalJSON)
            self.writeConfig()
            # ----------------------------------------
            sys.exit()

    def getConfig(self, key):
        with open(self.cfgFile, 'r') as openfile:
            json_object = json.load(openfile)

        return json_object[key]

    def writeConfig(self):
        if not os.path.isdir(os.path.dirname(self.cfgFile)):
            os.makedirs(os.path.dirname(self.cfgFile))

        # Serializing json
        json_object = json.dumps(self.globalJSON, indent=4)
        with open(self.cfgFile, 'w') as outfile:
            outfile.write(json_object)

    def updateConfig(self, data):
        self.globalJSON.update(data)

    def getVersion(self):
        pattern = "([0-9]+.[0-9]+.[0-9]+)"
        with open(self.aboutdialogFile, 'r') as f:
            for line in f.readlines():
                if re.search(pattern, line):
                    return re.search(pattern, line).group()


class ThreadNetworkStats(QtCore.QThread):
    signal = QtCore.pyqtSignal(dict, name='ThreadNetworkFinish')

    def __init__(self, parent=None):
        super(ThreadNetworkStats, self).__init__(parent)
        self.finished.connect(self.threadFinished)
        self.config = Config()
        self.iface = self.config.getConfig('iface')

    def threadFinished(self):
        self.start()

    def run(self):
        counter1 = psutil.net_io_counters(pernic=True)[self.iface]
        time.sleep(1)
        counter2 = psutil.net_io_counters(pernic=True)[self.iface]
        downSpeed = f'{humanfriendly.format_size(counter2.bytes_recv - counter1.bytes_recv)}/s'

        upSpeed = f'{humanfriendly.format_size(counter2.bytes_sent - counter1.bytes_sent)}/s'
        self.signal.emit({'downSpeed': downSpeed, 'upSpeed': upSpeed})


class ThreadSlow(QtCore.QThread):
    signal = QtCore.pyqtSignal(dict, name='ThreadSlowFinish')

    def __init__(self, parent=None):
        super(ThreadSlow, self).__init__(parent)
        self.finished.connect(self.threadFinished)
        self.config = Config()

    def threadFinished(self):
        self.start()

    def getPartitions(self):
        msg = []
        for mntPoint in self.config.getConfig('filesystems'):
            disk_usage = psutil.disk_usage(mntPoint)
            msg.append({
                'mountpoint': mntPoint,
                'total': humanfriendly.format_size(disk_usage.total),
                'used': humanfriendly.format_size(disk_usage.used),
                'free': humanfriendly.format_size(disk_usage.free),
                'percent': f'{disk_usage.percent}%'
            })

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
        # Config()
        self.config = Config()
        self.iface = self.config.getConfig('iface')
        # aboutdialog
        self.aboutDialog = QtWidgets.QDialog()
        uic.loadUi(f'{resource_path}/aboutdialog.ui', self.aboutDialog)
        self.aboutDialog.okPushButton = self.aboutDialog.findChild(QtWidgets.QPushButton, 'okPushButton')
        self.aboutDialog.okPushButton.clicked.connect(self.quitAboutDialog)
        self.version = self.aboutDialog.findChild(QtWidgets.QLabel, 'versionLabel').text()
        print(color(':: ', fore=11), color(f'Gonha {self.version}', fore=14, back=0), color(' ::', fore=11))
        print('Starting...')
        print()

        # Window Flags
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
        self.ew = EWMH()
        self.all_wins = self.ew.getClientList()
        self.wins = filter(lambda w: w.get_wm_class()[1] == 'gonha', self.all_wins)
        for w in self.wins:
            print(w)
            self.ew.setWmDesktop(w, 0xffffffff)

        self.ew.display.flush()
        self.threadFast.start()
        self.threadSlow.start()
        self.threadNetworkStats.start()
        self.loadConfigs()
        self.displayPartitions()
        print(':: Gonha version {} ::'.format(self.version))

    def quitAboutDialog(self):
        self.aboutDialog.hide()

    def receiveThreadNetworkStats(self, message):
        # print(message)
        self.ifaceValueLabel.setText(self.iface)
        self.downloadValueLabel.setText(message['downSpeed'])
        self.uploadValueLabel.setText(message['upSpeed'])

    def displayPartitions(self):
        font = QtGui.QFont('Fira Code', 11)
        orange = 'color: rgb(252, 126, 0);'
        white = 'color: rgb(255, 255, 255);'
        mntPoints = self.threadSlow.getPartitions()
        # print(mntPoints)
        for mntPoint in mntPoints:
            horizontalLayout = QtWidgets.QHBoxLayout()

            #
            mountpointValueLabel = QtWidgets.QLabel(mntPoint['mountpoint'])
            mountpointValueLabel.setFont(font)
            mountpointValueLabel.setStyleSheet(white)
            horizontalLayout.addWidget(mountpointValueLabel)

            usedLabel = QtWidgets.QLabel('used:')
            usedLabel.setStyleSheet(orange)
            usedLabel.setFont(font)
            usedLabel.setStyleSheet('color: rgb(252, 126, 0);')
            horizontalLayout.addWidget(usedLabel)

            usedValueLabel = QtWidgets.QLabel(mntPoint['used'])
            usedValueLabel.setFont(font)
            usedValueLabel.setStyleSheet(white)
            horizontalLayout.addWidget(usedValueLabel)

            totalLabel = QtWidgets.QLabel('total:')
            totalLabel.setStyleSheet(orange)
            horizontalLayout.addWidget(totalLabel)

            totalValueLabel = QtWidgets.QLabel(mntPoint['total'])
            totalValueLabel.setFont(font)
            totalValueLabel.setStyleSheet(white)
            horizontalLayout.addWidget(totalValueLabel)

            percentLabel = QtWidgets.QLabel('percent:')
            percentLabel.setStyleSheet(orange)
            percentLabel.setFont(font)
            horizontalLayout.addWidget(percentLabel)

            percentValueLabel = QtWidgets.QLabel(mntPoint['percent'])
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

            self.fsVerticalLayout.addLayout(horizontalLayout)

    def loadConfigs(self):
        # Adjust initial position
        if self.config.getConfig('position') == 'Top Left':
            self.moveTopLeft()
        else:
            self.moveTopRight()

        # lsbParser
        distroInfo = ConfigObj('/etc/lsb-release')
        self.lsbreleaseLabel.setText(
            f"{distroInfo['DISTRIB_DESCRIPTION']}"
        )

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        contextMenu = QtWidgets.QMenu(self)
        # topLeftAction = contextMenu.addAction('Top Left')
        # topRightAction = contextMenu.addAction('Top Right')
        # aboutAction = contextMenu.addAction('A&bout')
        quitAction = contextMenu.addAction('&Quit')
        action = contextMenu.exec_(self.mapToGlobal(event.pos()))
        if action == quitAction:
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
