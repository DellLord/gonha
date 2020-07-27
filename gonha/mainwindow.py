import sys
from PyQt5 import QtWidgets, QtGui
from ewmh import EWMH
from gonha.threads import *
from colr import color


class MainWindow(QtWidgets.QMainWindow):
    config = Config()
    iface = config.getConfig('iface')
    version = config.getVersion()
    app = QtWidgets.QApplication(sys.argv)
    threadNetworkStats = ThreadNetworkStats()
    threadFast = ThreadFast()
    threadSlow = ThreadSlow()
    partitionsWidgets = []
    upDownRateWidgets = []
    dtWidgets = dict()
    systemWidgets = dict()
    verticalLayout = QtWidgets.QVBoxLayout()

    def __init__(self):
        super(MainWindow, self).__init__()
        print(color(':: ', fore=11), color(f'Gonha {self.version}', fore=14, back=0), color(' ::', fore=11))
        print('Starting...')
        print()
        # -------------------------------------------------------------
        # Window Flags
        flags = QtCore.Qt.FramelessWindowHint
        flags |= QtCore.Qt.WindowStaysOnBottomHint
        flags |= QtCore.Qt.Tool
        # -------------------------------------------------------------
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
        QProgressBar {
            text-align: left;
            font-weight: bold;
            color: rgb(255, 255, 255);
            background-color : rgba(0, 0, 0, 0);
            border: 0px solid rgba(0, 0, 0, 0);
            border-radius: 3px;                                    
        }
        QProgressBar::chunk {
            background: rgb(255, 51, 0);
            border-radius: 3px;
        }
        """
        self.greenPBStyle = """
        QProgressBar {
            text-align: left;
            font-weight: bold;
            color: rgb(255, 255, 255);
            background-color : rgba(0, 0, 0, 0);
            border: 0px solid rgba(0, 0, 0, 0);
            border-radius: 3px;           
        }
        QProgressBar::chunk {
            background: rgb(51, 153, 51);
            border-radius: 3px;            
        }
        """
        self.orange = 'color: rgb(252, 126, 0);'
        self.white = 'color: rgb(255, 255, 255);'
        self.green = 'color: rgb(34, 255, 19);'
        self.red = 'color: rgb(255, 48, 79);'
        # ---------------------------------------------------------------------
        # Default font
        self.fontDefault = QtGui.QFont('Fira Code', 11)
        self.fontGroupBox = QtGui.QFont('Fira Code', 14)
        # -------------------------------------------------------------
        self.verticalLayout.setAlignment(QtCore.Qt.AlignTop)

        # --------------------------------------------------------------
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        # Connect Threads Signals
        self.threadFast.signal.connect(self.receiveThreadFastfinish)
        self.threadSlow.signal.connect(self.receiveThreadSlowFinish)
        self.threadNetworkStats.signal.connect(self.receiveThreadNetworkStats)

        self.setMinimumSize(QtCore.QSize(490, 900))
        centralWidGet = QtWidgets.QWidget(self)
        centralWidGet.setLayout(self.verticalLayout)
        self.setCentralWidget(centralWidGet)
        self.show()

        # Show in all workspaces
        self.ew = EWMH()
        self.all_wins = self.ew.getClientList()
        self.wins = filter(lambda w: w.get_wm_class()[1] == 'gonha', self.all_wins)
        for w in self.wins:
            self.ew.setWmDesktop(w, 0xffffffff)

        self.ew.display.flush()

        self.threadFast.start()
        self.threadSlow.start()
        self.threadNetworkStats.start()

        self.loadPosition()
        self.displayDateTime()
        self.displaySystem()
        self.displayIface()
        self.displayPartitions()

    def receiveThreadNetworkStats(self, message):
        self.upDownRateWidgets[0].setText(message['iface'])
        self.upDownRateWidgets[1].setText('{}/s'.format(humanfriendly.format_size(message['downSpeed'])))
        self.upDownRateWidgets[2].setText('{}/s'.format(humanfriendly.format_size(message['upSpeed'])))
        self.upDownRateWidgets[3].setText(humanfriendly.format_size(message['bytesRcv']))
        self.upDownRateWidgets[4].setText(humanfriendly.format_size(message['bytesSent']))

    def displayIface(self):
        ifaceGroupBox = QtWidgets.QGroupBox('net')
        ifaceGroupBox.setFont(self.fontGroupBox)
        ifaceGroupBox.setStyleSheet(self.groupBoxStyle)
        verticalLayout = QtWidgets.QVBoxLayout()
        horizontalLayout = QtWidgets.QHBoxLayout()

        # -------------------------------------------------
        # iface Label
        ifaceLabel = QtWidgets.QLabel('interface:')
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
        downloadIcon.setPixmap(QtGui.QPixmap(f'{self.config.resource_path}/images/download.png'))
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
        uploadIcon.setPixmap(QtGui.QPixmap(f'{self.config.resource_path}/images/upload.png'))
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

        verticalLayout.addLayout(horizontalLayout)
        # ---------------------------------------------------

        # Total in
        bytesSentRcvHLayout = QtWidgets.QHBoxLayout()

        bytesRcvLabel = QtWidgets.QLabel('total in:')
        bytesRcvLabel.setFont(self.fontDefault)
        bytesRcvLabel.setStyleSheet(self.orange)
        bytesSentRcvHLayout.addWidget(bytesRcvLabel)

        bytesRcvValueLabel = QtWidgets.QLabel('123 bytes')
        bytesRcvValueLabel.setFont(self.fontDefault)
        bytesRcvValueLabel.setStyleSheet(self.white)
        bytesRcvValueLabel.setAlignment(QtCore.Qt.AlignRight)
        self.upDownRateWidgets.append(bytesRcvValueLabel)
        bytesSentRcvHLayout.addWidget(bytesRcvValueLabel)

        # Total out
        bytesSentLabel = QtWidgets.QLabel('total out:')
        bytesSentLabel.setFont(self.fontDefault)
        bytesSentLabel.setStyleSheet(self.orange)
        bytesSentRcvHLayout.addWidget(bytesSentLabel)

        bytesSentValueLabel = QtWidgets.QLabel('423 bytes')
        bytesSentValueLabel.setFont(self.fontDefault)
        bytesSentValueLabel.setStyleSheet(self.white)
        bytesSentValueLabel.setAlignment(QtCore.Qt.AlignRight)
        self.upDownRateWidgets.append(bytesSentValueLabel)
        bytesSentRcvHLayout.addWidget(bytesSentValueLabel)

        verticalLayout.addLayout(bytesSentRcvHLayout)

        ifaceGroupBox.setLayout(verticalLayout)
        self.verticalLayout.addWidget(ifaceGroupBox)

    def displayDateTime(self):
        timeFont = QtGui.QFont('Fira Code', 20)

        dateTimeGroupBox = QtWidgets.QGroupBox('datetime')
        dateTimeGroupBox.setFont(self.fontGroupBox)
        dateTimeGroupBox.setStyleSheet(self.groupBoxStyle)

        verticalLayout = QtWidgets.QVBoxLayout()

        dateTimeHBLayout = QtWidgets.QHBoxLayout()
        dateTimeHBLayout.setAlignment(QtCore.Qt.AlignHCenter)

        twoPointLabel = [QtWidgets.QLabel(':'), QtWidgets.QLabel(':')]
        twoPointLabel[0].setFont(timeFont)
        twoPointLabel[0].setStyleSheet(self.orange)
        twoPointLabel[1].setFont(timeFont)
        twoPointLabel[1].setStyleSheet(self.orange)

        hourLabel = QtWidgets.QLabel('02')
        hourLabel.setFont(timeFont)
        hourLabel.setStyleSheet(self.white)
        self.dtWidgets['hour'] = hourLabel

        minLabel = QtWidgets.QLabel('24')
        minLabel.setFont(timeFont)
        minLabel.setStyleSheet(self.white)
        self.dtWidgets['min'] = minLabel

        secLabel = QtWidgets.QLabel('32')
        secLabel.setFont(timeFont)
        secLabel.setStyleSheet(self.white)
        self.dtWidgets['sec'] = secLabel

        ampmLabel = QtWidgets.QLabel('pm')
        ampmLabel.setFont(timeFont)
        ampmLabel.setStyleSheet(self.orange)
        self.dtWidgets['ampm'] = ampmLabel

        dateTimeHBLayout.addWidget(hourLabel)
        dateTimeHBLayout.addWidget(twoPointLabel[0])
        dateTimeHBLayout.addWidget(minLabel)
        dateTimeHBLayout.addWidget(twoPointLabel[1])
        dateTimeHBLayout.addWidget(secLabel)
        dateTimeHBLayout.addWidget(ampmLabel)

        verticalLayout.addLayout(dateTimeHBLayout)

        # Now, add date
        dateHBLayout = QtWidgets.QHBoxLayout()
        dateHBLayout.setAlignment(QtCore.Qt.AlignHCenter)

        dateLabel = QtWidgets.QLabel('test')
        dateLabel.setFont(timeFont)
        dateLabel.setStyleSheet(self.white)
        self.dtWidgets['date'] = dateLabel

        dateHBLayout.addWidget(dateLabel)

        verticalLayout.addLayout(dateHBLayout)

        dateTimeGroupBox.setLayout(verticalLayout)
        dateTimeGroupBox.setMinimumHeight(40)
        self.verticalLayout.addWidget(dateTimeGroupBox)

    def displaySystem(self):
        labelDefaultWidth = 80

        systemGroupBox = QtWidgets.QGroupBox('system')
        systemGroupBox.setFont(self.fontGroupBox)
        systemGroupBox.setStyleSheet(self.groupBoxStyle)

        verticalLayout = QtWidgets.QVBoxLayout()
        # ---------------------------------------------------------------------------
        unamehboxLayout = QtWidgets.QHBoxLayout()
        # uname label
        codename = 'gonha'
        distroStr = f'teste'
        if codename == '':
            distroStr = f'teste'

        unameLabel = QtWidgets.QLabel(distroStr)
        unameLabel.setFont(self.fontDefault)
        unameLabel.setStyleSheet(self.white)
        unameLabel.setAlignment(QtCore.Qt.AlignCenter)
        unamehboxLayout.addWidget(unameLabel)

        verticalLayout.addLayout(unamehboxLayout)
        # ---------------------------------------------------------------------------
        # boot time label
        bootTimeHboxLayout = QtWidgets.QHBoxLayout()

        bootTimeValueLabel = QtWidgets.QLabel()
        bootTimeValueLabel.setFont(self.fontDefault)
        bootTimeValueLabel.setStyleSheet(self.white)
        bootTimeValueLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.systemWidgets['boottime'] = bootTimeValueLabel
        bootTimeHboxLayout.addWidget(bootTimeValueLabel)

        verticalLayout.addLayout(bootTimeHboxLayout)
        # ---------------------------------------------------------------------------
        cpuHBLayout = QtWidgets.QHBoxLayout()

        cpuBrandLabel = QtWidgets.QLabel(self.config.getConfig('cpuinfo'))
        cpuBrandLabel.setFont(self.fontDefault)
        cpuBrandLabel.setStyleSheet(self.white)
        cpuBrandLabel.setAlignment(QtCore.Qt.AlignHCenter)
        cpuHBLayout.addWidget(cpuBrandLabel)

        verticalLayout.addLayout(cpuHBLayout)

        # Cpu load
        cpuLoadHBLayout = QtWidgets.QHBoxLayout()
        cpuLoadLabel = QtWidgets.QLabel('cpu:')
        cpuLoadLabel.setFixedWidth(labelDefaultWidth)
        cpuLoadLabel.setFont(self.fontDefault)
        cpuLoadLabel.setStyleSheet(self.orange)
        cpuLoadHBLayout.addWidget(cpuLoadLabel)

        cpuProgressBar = QtWidgets.QProgressBar()
        cpuProgressBar.setFont(self.fontDefault)
        cpuProgressBar.setStyleSheet(self.greenPBStyle)
        cpuProgressBar.setValue(12)
        self.systemWidgets['cpuProgressBar'] = cpuProgressBar

        cpuLoadHBLayout.addWidget(cpuProgressBar)

        cpuFreqLabel = QtWidgets.QLabel('14343.34 Mhz')
        cpuFreqLabel.setFont(self.fontDefault)
        self.systemWidgets['cpufreq'] = cpuFreqLabel
        cpuFreqLabel.setStyleSheet(self.white)

        cpuLoadHBLayout.addWidget(cpuFreqLabel)

        verticalLayout.addLayout(cpuLoadHBLayout)

        # ---------------------------------------------------------------------------
        # ram load
        ramLoadHBLayout = QtWidgets.QHBoxLayout()

        ramLoadLabel = QtWidgets.QLabel('ram:')
        ramLoadLabel.setFixedWidth(labelDefaultWidth)
        ramLoadLabel.setFont(self.fontDefault)
        ramLoadLabel.setStyleSheet(self.orange)

        ramLoadHBLayout.addWidget(ramLoadLabel)

        ramProgressBar = QtWidgets.QProgressBar()
        ramProgressBar.setFont(self.fontDefault)
        ramProgressBar.setStyleSheet(self.greenPBStyle)
        self.systemWidgets['ramProgressBar'] = ramProgressBar
        ramProgressBar.setValue(32)

        ramLoadHBLayout.addWidget(ramProgressBar)

        ramUsedLabel = QtWidgets.QLabel('15443 MB')
        ramUsedLabel.setFont(self.fontDefault)
        ramUsedLabel.setStyleSheet(self.white)
        self.systemWidgets['ramused'] = ramUsedLabel

        ramLoadHBLayout.addWidget(ramUsedLabel)

        verticalLayout.addLayout(ramLoadHBLayout)
        # ---------------------------------------------------------------------------
        # swap load
        swapHBLayout = QtWidgets.QHBoxLayout()

        swapLabel = QtWidgets.QLabel('swap:')
        swapLabel.setFixedWidth(labelDefaultWidth)
        swapLabel.setFont(self.fontDefault)
        swapLabel.setStyleSheet(self.orange)

        swapHBLayout.addWidget(swapLabel)

        swapProgressBar = QtWidgets.QProgressBar()
        swapProgressBar.setFont(self.fontDefault)
        swapProgressBar.setStyleSheet(self.greenPBStyle)
        self.systemWidgets['swapProgressBar'] = swapProgressBar
        swapProgressBar.setValue(52)

        swapHBLayout.addWidget(swapProgressBar)

        swapUsedLabel = QtWidgets.QLabel('16654 MB')
        swapUsedLabel.setFont(self.fontDefault)
        swapUsedLabel.setStyleSheet(self.white)
        self.systemWidgets['swapused'] = swapUsedLabel

        swapHBLayout.addWidget(swapUsedLabel)

        verticalLayout.addLayout(swapHBLayout)

        # ---------------------------------------------------------------------------
        # Temperature
        tempHBLayout = QtWidgets.QHBoxLayout()

        tempLabel = QtWidgets.QLabel('temp:')
        tempLabel.setFixedWidth(labelDefaultWidth)
        tempLabel.setFont(self.fontDefault)
        tempLabel.setStyleSheet(self.orange)

        tempHBLayout.addWidget(tempLabel)

        tempValueLabel = QtWidgets.QLabel('label')
        self.systemWidgets['label'] = tempValueLabel
        tempValueLabel.setFont(self.fontDefault)
        tempValueLabel.setStyleSheet(self.white)

        tempHBLayout.addWidget(tempValueLabel)

        tempCurrentLabel = QtWidgets.QLabel('current:')
        tempCurrentLabel.setFont(self.fontDefault)
        tempCurrentLabel.setFixedWidth(labelDefaultWidth)
        tempCurrentLabel.setStyleSheet(self.orange)

        tempHBLayout.addWidget(tempCurrentLabel)

        tempCurrentValueLabel = QtWidgets.QLabel('30C')
        tempCurrentValueLabel.setFont(self.fontDefault)
        self.systemWidgets['current'] = tempCurrentValueLabel
        tempCurrentValueLabel.setStyleSheet(self.white)

        tempHBLayout.addWidget(tempCurrentValueLabel)

        verticalLayout.addLayout(tempHBLayout)

        # ---------------------------------------------------------------------------
        systemGroupBox.setLayout(verticalLayout)
        self.verticalLayout.addWidget(systemGroupBox)

    def displayPartitions(self):
        mntPoints = self.threadSlow.getPartitions()
        diskGroupBox = QtWidgets.QGroupBox('disks')
        diskGroupBox.setFont(self.fontGroupBox)
        diskGroupBox.setStyleSheet(self.groupBoxStyle)
        verticalLayout = QtWidgets.QVBoxLayout()
        verticalLayout.setAlignment(QtCore.Qt.AlignTop)
        height = 0
        pbFixedWidth = 260
        labelAlignment = (QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        labelDefaultWidth = 80

        for mntPoint in mntPoints:
            mountpointHorizontalLayout = QtWidgets.QHBoxLayout()

            # ------------- mountpoint ----------------------
            mountpointValueLabel = QtWidgets.QLabel(mntPoint['mountpoint'])
            mountpointValueLabel.setFont(self.fontDefault)
            mountpointValueLabel.setStyleSheet(self.white)
            mountpointHorizontalLayout.addWidget(mountpointValueLabel)

            totalValueLabel = QtWidgets.QLabel(mntPoint['total'])
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
            usedLabel.setFixedWidth(labelDefaultWidth)
            usedHorizontalLayout.addWidget(usedLabel)

            # ProgressBar
            usedPB = QtWidgets.QProgressBar()
            usedPB.setFont(self.fontDefault)
            usedPB.setStyleSheet(self.redPBStyle)
            usedPB.setFixedWidth(pbFixedWidth)
            usedPB.setValue(mntPoint['percentUsed'])

            usedHorizontalLayout.addWidget(usedPB)

            usedValueLabel = QtWidgets.QLabel(mntPoint['used'])
            usedValueLabel.setFont(self.fontDefault)
            usedValueLabel.setStyleSheet(self.white)
            usedValueLabel.setAlignment(labelAlignment)

            usedHorizontalLayout.addWidget(usedValueLabel)

            verticalLayout.addLayout(usedHorizontalLayout)
            # ----------------------------------------------------------
            # free stats
            freeHorizontalLayout = QtWidgets.QHBoxLayout()
            freeLabel = QtWidgets.QLabel('free:')
            freeLabel.setFont(self.fontDefault)
            freeLabel.setStyleSheet(self.orange)
            freeLabel.setFixedWidth(labelDefaultWidth)
            freeHorizontalLayout.addWidget(freeLabel)

            freePB = QtWidgets.QProgressBar()
            freePB.setFont(self.fontDefault)
            freePB.setStyleSheet(self.greenPBStyle)
            freePB.setFixedWidth(pbFixedWidth)
            freePB.setAlignment(QtCore.Qt.AlignLeft)
            freePB.setValue(mntPoint['percentFree'])

            freeHorizontalLayout.addWidget(freePB)

            freeValueLabel = QtWidgets.QLabel(mntPoint['free'])
            freeValueLabel.setFont(self.fontDefault)
            freeValueLabel.setStyleSheet(self.white)
            freeValueLabel.setAlignment(labelAlignment)
            freeHorizontalLayout.addWidget(freeValueLabel)

            verticalLayout.addLayout(freeHorizontalLayout)

            # ----------------------------------------------------------

            height = height + 105

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

    def loadPosition(self):
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
        screen = self.app.primaryScreen()
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
            widget['totalValueLabel'].setText(message[i]['total'])
            widget['usedValueLabel'].setText(message[i]['used'])
            widget['usedPB'].setValue(message[i]['percentUsed'])
            widget['freeValueLabel'].setText(message[i]['free'])
            widget['freePB'].setValue(message[i]['percentFree'])

    def receiveThreadFastfinish(self, message):
        self.dtWidgets['hour'].setText(message['hour'])
        self.dtWidgets['min'].setText(message['min'])
        self.dtWidgets['sec'].setText(message['sec'])
        self.dtWidgets['ampm'].setText(message['ampm'])
        self.dtWidgets['date'].setText(message['date'])
        # --------------------------------------------------------
        # update cpu load
        self.systemWidgets['cpuProgressBar'].setValue(message['cpuProgressBar'])
        self.systemWidgets['ramProgressBar'].setValue(message['ramProgressBar'])
        self.systemWidgets['swapProgressBar'].setValue(message['swapProgressBar'])
        # ----------------------------
        # update temperature
        self.systemWidgets['label'].setText(message['label'])
        self.systemWidgets['current'].setText(message['current'])

        self.systemWidgets['cpufreq'].setText(message['cpufreq'])
        self.systemWidgets['ramused'].setText(message['ramused'])
        self.systemWidgets['swapused'].setText(message['swapused'])

        self.systemWidgets['boottime'].setText(message['boottime'])

        current = int(''.join(filter(str.isdigit, message['current'])))
        critical = 80
        if current >= critical:
            self.systemWidgets['current'].setStyleSheet(self.red)
        else:
            self.systemWidgets['current'].setStyleSheet(self.green)
