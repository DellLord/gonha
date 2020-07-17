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
import distro
import humanize

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
        self.signal.emit({'downSpeed': downSpeed, 'upSpeed': upSpeed, 'iface': self.iface})


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
    partitionsWidgets = []
    upDownRateWidgets = []

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
        self.temperatureValueLabel = self.findChild(QtWidgets.QLabel, 'temperatureValueLabel')
        # ---------------------------------------------------------------------
        # Styles
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
        self.redPBStyle = """
        QProgressBar::value {
            font-weight: bold;
        }
        QProgressBar {
            text-align: left;
        }
        QProgressBar::chunk {
            background: rgb(255, 51, 0);
            font-weight: bold;
        }        
        """
        self.greenPBStyle = """
        QProgressBar {
            text-align: left;
        }
        QProgressBar::chunk {
            background: rgb(51, 153, 51);
            font-weight: bold;
        }        
        """
        self.orange = 'color: rgb(252, 126, 0);'
        self.white = 'color: rgb(255, 255, 255);'
        self.green = 'color: rgb(0, 204, 0);'
        # ---------------------------------------------------------------------
        # Default font
        self.fontDefault = QtGui.QFont('Fira Code', 11)
        self.fontGroupBox = QtGui.QFont('Fira Code', 14)
        # -------------------------------------------------------------
        self.verticalLayout = self.findChild(QtWidgets.QVBoxLayout, 'verticalLayout')
        self.verticalLayout.setAlignment(QtCore.Qt.AlignTop)
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
        self.displaySystem()
        self.displayIface()
        self.displayPartitions()

    def receiveThreadNetworkStats(self, message):
        self.upDownRateWidgets[0].setText(message['iface'])
        self.upDownRateWidgets[1].setText(message['downSpeed'])
        self.upDownRateWidgets[2].setText(message['upSpeed'])

        # self.downloadValueLabel.setText(message['downSpeed'])
        # self.uploadValueLabel.setText(message['upSpeed'])

    def displayIface(self):
        ifaceGroupBox = QtWidgets.QGroupBox('iface')
        ifaceGroupBox.setFont(self.fontGroupBox)
        ifaceGroupBox.setStyleSheet(self.groupBoxStyle)
        verticalLayout = QtWidgets.QVBoxLayout()
        horizontalLayout = QtWidgets.QHBoxLayout()

        # -------------------------------------------------
        # iface Label
        ifaceLabel = QtWidgets.QLabel('iface:')
        ifaceLabel.setFont(self.fontDefault)
        ifaceLabel.setStyleSheet(self.orange)
        ifaceLabel.setAlignment(QtCore.Qt.AlignLeft)
        horizontalLayout.addWidget(ifaceLabel)

        # -------------------------------------------------
        # ifaceValueLabel
        ifaceValueLabel = QtWidgets.QLabel('enp6s1')
        ifaceValueLabel.setFont(self.fontDefault)
        ifaceValueLabel.setStyleSheet(self.white)
        ifaceValueLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.upDownRateWidgets.append(ifaceValueLabel)
        horizontalLayout.addWidget(ifaceValueLabel)

        # -------------------------------------------------
        # Download Icon
        downloadIcon = QtWidgets.QLabel()
        downloadIcon.setPixmap(QtGui.QPixmap(f'{resource_path}/images/download.png'))
        horizontalLayout.addWidget(downloadIcon)
        # -------------------------------------------------

        # ---------------------------------------------------
        # download rate label
        ifaceDownRateLabel = QtWidgets.QLabel('480 kb/s')
        ifaceDownRateLabel.setFont(self.fontDefault)
        ifaceDownRateLabel.setStyleSheet(self.white)
        ifaceDownRateLabel.setAlignment(QtCore.Qt.AlignRight)
        ifaceDownRateLabel.setFixedWidth(110)
        self.upDownRateWidgets.append(ifaceDownRateLabel)
        horizontalLayout.addWidget(ifaceDownRateLabel)
        # ---------------------------------------------------

        # -------------------------------------------------
        # Upload Icon
        uploadIcon = QtWidgets.QLabel()
        uploadIcon.setPixmap(QtGui.QPixmap(f'{resource_path}/images/upload.png'))
        horizontalLayout.addWidget(uploadIcon)
        # -------------------------------------------------

        # ---------------------------------------------------
        # upload rate label
        ifaceUpRateLabel = QtWidgets.QLabel('180 kb/s')
        ifaceUpRateLabel.setFont(self.fontDefault)
        ifaceUpRateLabel.setStyleSheet(self.white)
        ifaceUpRateLabel.setAlignment(QtCore.Qt.AlignRight)
        ifaceUpRateLabel.setFixedWidth(110)
        self.upDownRateWidgets.append(ifaceUpRateLabel)
        horizontalLayout.addWidget(ifaceUpRateLabel)
        # ---------------------------------------------------

        verticalLayout.addLayout(horizontalLayout)
        ifaceGroupBox.setLayout(verticalLayout)
        self.verticalLayout.addWidget(ifaceGroupBox)

    def displaySystem(self):

        distroLinux = distro.linux_distribution()

        unameGroupBox = QtWidgets.QGroupBox('system')
        unameGroupBox.setFont(self.fontGroupBox)
        unameGroupBox.setStyleSheet(self.groupBoxStyle)
        verticalLayout = QtWidgets.QVBoxLayout()
        # ---------------------------------------------------------------------------
        unamehboxLayout = QtWidgets.QHBoxLayout()
        # uname label
        unameLabel = QtWidgets.QLabel(f'{distroLinux[0]} {distroLinux[1]} codename {distroLinux[2]}')
        unameLabel.setFont(self.fontDefault)
        unameLabel.setStyleSheet(self.white)
        unameLabel.setAlignment(QtCore.Qt.AlignCenter)
        unamehboxLayout.addWidget(unameLabel)

        verticalLayout.addLayout(unamehboxLayout)
        # ---------------------------------------------------------------------------

        # ---------------------------------------------------------------------------
        # boot time label
        bootTimeHboxLayout = QtWidgets.QHBoxLayout()

        bootTimeLabel = QtWidgets.QLabel(
            datetime.fromtimestamp(psutil.boot_time()).strftime('%H hours, %M minutes and %S seconds')
        )
        bootTimeLabel.setFont(self.fontDefault)
        bootTimeLabel.setStyleSheet(self.white)
        bootTimeLabel.setAlignment(QtCore.Qt.AlignCenter)
        bootTimeHboxLayout.addWidget(bootTimeLabel)

        verticalLayout.addLayout(bootTimeHboxLayout)

        # ---------------------------------------------------------------------------
        unameGroupBox.setLayout(verticalLayout)
        self.verticalLayout.addWidget(unameGroupBox)

    def displayPartitions(self):
        mntPoints = self.threadSlow.getPartitions()
        diskGroupBox = QtWidgets.QGroupBox('disks')
        diskGroupBox.setFont(self.fontGroupBox)
        diskGroupBox.setStyleSheet(self.groupBoxStyle)
        verticalLayout = QtWidgets.QVBoxLayout()
        verticalLayout.setAlignment(QtCore.Qt.AlignTop)
        height = 0

        for mntPoint in mntPoints:
            mountpointHorizontalLayout = QtWidgets.QHBoxLayout()

            # ------------- mountpoint ----------------------
            mountpointValueLabel = QtWidgets.QLabel(mntPoint['mountpoint'])
            mountpointValueLabel.setFont(self.fontDefault)
            mountpointValueLabel.setStyleSheet(self.white)
            mountpointHorizontalLayout.addWidget(mountpointValueLabel)

            totalValueLabel = QtWidgets.QLabel(humanfriendly.format_size(mntPoint['total']))
            totalValueLabel.setFont(self.fontDefault)
            totalValueLabel.setStyleSheet(self.white)
            totalValueLabel.setAlignment(QtCore.Qt.AlignRight)
            mountpointHorizontalLayout.addWidget(totalValueLabel)

            verticalLayout.addLayout(mountpointHorizontalLayout)
            # ----------------------------------------------------------
            # used stats
            usedHorizontalLayout = QtWidgets.QHBoxLayout()
            usedLabel = QtWidgets.QLabel('used:')
            usedLabel.setFont(self.fontDefault)
            usedLabel.setStyleSheet(self.orange)
            usedHorizontalLayout.addWidget(usedLabel)

            usedValueLabel = QtWidgets.QLabel(humanfriendly.format_size(mntPoint['used']))
            usedValueLabel.setFont(self.fontDefault)
            usedValueLabel.setStyleSheet(self.white)
            usedValueLabel.setAlignment(QtCore.Qt.AlignRight)
            usedHorizontalLayout.addWidget(usedValueLabel)

            verticalLayout.addLayout(usedHorizontalLayout)

            # ProgressBar
            usedPBLayout = QtWidgets.QHBoxLayout()
            usedPB = QtWidgets.QProgressBar()
            usedPB.setFont(self.fontDefault)
            usedPB.setStyleSheet(self.redPBStyle)
            usedPB.setValue(self.getValueInt(mntPoint['used'], mntPoint['total']))
            usedPBLayout.addWidget(usedPB)

            verticalLayout.addLayout(usedPBLayout)

            # ----------------------------------------------------------
            # free stats
            freeHorizontalLayout = QtWidgets.QHBoxLayout()
            freeLabel = QtWidgets.QLabel('free:')
            freeLabel.setFont(self.fontDefault)
            freeLabel.setStyleSheet(self.orange)
            freeHorizontalLayout.addWidget(freeLabel)

            freeValueLabel = QtWidgets.QLabel(humanfriendly.format_size(mntPoint['free']))
            freeValueLabel.setFont(self.fontDefault)
            freeValueLabel.setStyleSheet(self.white)
            freeValueLabel.setAlignment(QtCore.Qt.AlignRight)
            freeHorizontalLayout.addWidget(freeValueLabel)

            verticalLayout.addLayout(freeHorizontalLayout)

            freePBHLayout = QtWidgets.QHBoxLayout()
            freePB = QtWidgets.QProgressBar()
            freePB.setFont(self.fontDefault)
            freePB.setStyleSheet(self.greenPBStyle)
            freePB.setValue(self.getValueInt(mntPoint['free'], mntPoint['total']))
            freePBHLayout.addWidget(freePB)

            verticalLayout.addLayout(freePBHLayout)

            # ----------------------------------------------------------

            height = height + 120

            self.partitionsWidgets.append(
                {
                    'mountpointValueLabel': mountpointValueLabel,
                    'totalValueLabel': totalValueLabel,
                    'usedValueLabel': usedValueLabel,
                    'usedPB': usedPB,
                    'freeValueLabel': freeValueLabel,
                    'freePB': freePB
                }
            )

        diskGroupBox.setLayout(verticalLayout)
        diskGroupBox.setMinimumHeight(height)
        self.verticalLayout.addWidget(diskGroupBox)

    @staticmethod
    def getValueInt(val1, val2):
        free = float(val1)
        total = float(val2)
        return int((free * 100) / total)

    def loadConfigs(self):
        # Adjust initial position
        if self.config.getConfig('position') == 'Top Left':
            self.moveTopLeft()
        else:
            self.moveTopRight()

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        contextMenu = QtWidgets.QMenu(self)
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
        for i, widget in enumerate(self.partitionsWidgets):
            widget['mountpointValueLabel'].setText(message[i]['mountpoint'])
            widget['totalValueLabel'].setText(humanfriendly.format_size(message[i]['total']))
            widget['usedValueLabel'].setText(humanfriendly.format_size(message[i]['used']))
            widget['usedPB'].setValue(self.getValueInt(message[i]['used'], message[i]['total']))
            widget['freeValueLabel'].setText(humanfriendly.format_size(message[i]['free']))
            widget['freePB'].setValue(self.getValueInt(message[i]['free'], message[i]['total']))

    def receiveThreadFastfinish(self, message):
        self.hourLabel.setText(message['hourLabel'])
        self.minuteLabel.setText(message['minuteLabel'])
        self.ampmLabel.setText(message['ampmLabel'])
        self.dateLabel.setText(message['dateLabel'])
        self.memValueLabel.setText(message['memValueLabel'])
        self.cpuValueLabel.setText(message['cpuValueLabel'])
        self.temperatureValueLabel.setText(message['temperatureValueLabel'])
