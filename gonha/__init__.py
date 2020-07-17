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
        self.mainWindowFile = f'{resource_path}/mainwindow.ui'
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
                    '{} - [{}] current temp: {:.2f}°'.format(i, key, float(sensors[key][0].current))
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

            print(color("That´s ", fore=10), color('OK', fore=11))
            print(color('Now, you can running', fore=10), color('gonha', fore=11),
                  color('command again with all config options for your system!', fore=10))
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
        with open(self.mainWindowFile, 'r') as f:
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
    signal = QtCore.pyqtSignal(list, name='ThreadSlowFinish')

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
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free,
                'percent': disk_usage.percent
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
        self.config = Config()

    def threadFinished(self):
        self.start()

    def run(self):
        now = datetime.now()
        dateFormat = self.config.getConfig('dateFormat')
        if dateFormat == '24 hours':
            self.message['hourLabel'] = now.strftime('%H')
            self.message['ampmLabel'] = ''
        else:
            self.message['hourLabel'] = now.strftime('%I')
            self.message['ampmLabel'] = now.strftime('%p')

        self.message['minuteLabel'] = now.strftime('%M')
        self.message['secondsLabel'] = now.strftime('%S')
        self.message['dateLabel'] = now.strftime("%A, %d %B %Y")
        self.message['cpuValueLabel'] = f"{psutil.cpu_percent()}%"
        self.message['memValueLabel'] = f"{psutil.virtual_memory().percent}%"

        sensorIndex = int(self.config.getConfig('temp'))
        sensors = psutil.sensors_temperatures()
        for i, key in enumerate(sensors):
            if i == sensorIndex:
                self.message['temperatureValueLabel'] = '{:.2f}°'.format(float(sensors[key][0].current))
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
        self.version = self.windowTitle()
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
        self.ifaceValueLabel = self.findChild(QtWidgets.QLabel, 'ifaceValueLabel')
        self.downloadValueLabel = self.findChild(QtWidgets.QLabel, 'downloadValueLabel')
        self.uploadValueLabel = self.findChild(QtWidgets.QLabel, 'uploadValueLabel')
        self.groupBoxStyle = """
        QGroupBox {
            border: 1px solid white;
            border-radius: 5px;
            margin-top: 12px;
            padding-left: 2px;
        }
        QGroupBox:title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            color: rgb(252, 126, 0);
            left: 15px;
        }
        """
        # -------------------------------------------------------------
        self.centralwidget = self.findChild(QtWidgets.QWidget, 'centralwidget')  # Get Central widget
        self.netGroupBox = self.findChild(QtWidgets.QGroupBox, 'netGroupBox')
        self.netGroupBox.setStyleSheet(self.groupBoxStyle)
        self.fsGroupBox = self.findChild(QtWidgets.QGroupBox, 'fsGroupBox')
        self.fsGroupBox.setStyleSheet(self.groupBoxStyle)
        # --------------------------------------------------------------
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
        verticalLayout = QtWidgets.QVBoxLayout()
        verticalLayout.setAlignment(QtCore.Qt.AlignTop)
        height = 0
        fsGroupBox = QtWidgets.QGroupBox('disks')
        fsGroupBox.setStyleSheet(self.groupBoxStyle)
        progressBarStyle = """
        QProgressBar {
            text-align: center;
        }
        QProgressBar::chunk {
            background: rgb(255, 51, 0);
            font-weight: bold;
        }        
        """
        for mntPoint in mntPoints:
            mountpointHorizontalLayout = QtWidgets.QHBoxLayout()

            # ------------- mountpoint ----------------------
            mountpointValueLabel = QtWidgets.QLabel(mntPoint['mountpoint'])
            mountpointValueLabel.setFont(font)
            mountpointValueLabel.setStyleSheet(white)
            mountpointHorizontalLayout.addWidget(mountpointValueLabel)

            print(humanfriendly.format_size(mntPoint['total']))
            totalValueLabel = QtWidgets.QLabel(humanfriendly.format_size(mntPoint['total']))
            totalValueLabel.setFont(font)
            totalValueLabel.setStyleSheet(white)
            totalValueLabel.setAlignment(QtCore.Qt.AlignRight)
            mountpointHorizontalLayout.addWidget(totalValueLabel)

            verticalLayout.addLayout(mountpointHorizontalLayout)
            # ----------------------------------------------------------

            # used stats
            usedHorizontalLayout = QtWidgets.QHBoxLayout()
            usedLabel = QtWidgets.QLabel('used:')
            usedLabel.setFont(font)
            usedLabel.setStyleSheet(orange)
            usedHorizontalLayout.addWidget(usedLabel)

            usedValueLabel = QtWidgets.QLabel(humanfriendly.format_size(mntPoint['used']))
            usedValueLabel.setFont(font)
            usedValueLabel.setStyleSheet(white)
            usedValueLabel.setAlignment(QtCore.Qt.AlignRight)
            usedHorizontalLayout.addWidget(usedValueLabel)

            verticalLayout.addLayout(usedHorizontalLayout)
            # ----------------------------------------------------------
            # ProgressBar
            usedPBHLayout = QtWidgets.QHBoxLayout()
            usedPB = QtWidgets.QProgressBar()
            usedPB.setFont(font)
            usedPB.setStyleSheet(progressBarStyle)
            used = float(mntPoint['used'])
            total = float(mntPoint['total'])
            usedPB.setValue(int((used * 100) / total))
            usedPBHLayout.addWidget(usedPB)

            verticalLayout.addLayout(usedPBHLayout)

            # free stats
            freeHorizontalLayout = QtWidgets.QHBoxLayout()
            freeLabel = QtWidgets.QLabel('free:')
            freeLabel.setFont(font)
            freeLabel.setStyleSheet(orange)
            freeHorizontalLayout.addWidget(freeLabel)

            freeValueLabel = QtWidgets.QLabel(humanfriendly.format_size(mntPoint['free']))
            freeValueLabel.setFont(font)
            freeValueLabel.setStyleSheet(white)
            freeValueLabel.setAlignment(QtCore.Qt.AlignRight)
            freeHorizontalLayout.addWidget(freeValueLabel)

            verticalLayout.addLayout(freeHorizontalLayout)
            # ----------------------------------------------------------

            height = height + 100

            self.partitionsLabels.append(
                {
                    'mountpointValueLabel': mountpointValueLabel,
                    'usedValueLabel': totalValueLabel
                }
            )

        self.fsGroupBox.setLayout(verticalLayout)
        self.fsGroupBox.setMinimumHeight(height)

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
            label['mountpointValueLabel'].setText(message[i]['mountpoint'])
            label['usedValueLabel'].setText(message[i]['used'])
            label['totalValueLabel'].setText(message[i]['total'])
            label['percentValueLabel'].setText(message[i]['percent'])

    def receiveThreadFastfinish(self, message):
        self.hourLabel.setText(message['hourLabel'])
        self.minuteLabel.setText(message['minuteLabel'])
        self.ampmLabel.setText(message['ampmLabel'])
        self.dateLabel.setText(message['dateLabel'])
        self.memValueLabel.setText(message['memValueLabel'])
        self.cpuValueLabel.setText(message['cpuValueLabel'])
        self.temperatureValueLabel.setText(message['temperatureValueLabel'])
