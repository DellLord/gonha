import sys
from PyQt5 import QtWidgets, QtGui
from ewmh import EWMH
from gonha.threads import *
from colr import color
from gonha.util import Weather
from country_list import countries_for_language


class MainWindow(QtWidgets.QMainWindow):
    config = Config()
    iface = config.getConfig('iface')
    version = config.getVersion()
    app = QtWidgets.QApplication(sys.argv)
    threadNetworkStats = ThreadNetworkStats()
    threadFast = ThreadFast()
    threadSlow = ThreadSlow()
    threadweather = ThreadWeather()
    partitionsWidgets = []
    upDownRateWidgets = []
    dtwWidgets = dict()
    systemWidgets = dict()
    verticalLayout = QtWidgets.QVBoxLayout()
    weather = Weather()

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
        self.threadweather.signal.connect(self.receiveThreadWeatherFinish)

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
        self.displayDTWeather()
        # self.displayweather()
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
        # ---------------------------------------------------
        # Ip int Label
        ipintHBLayout = QtWidgets.QHBoxLayout()

        intipLabel = QtWidgets.QLabel('int. IP:')
        intipLabel.setFont(self.fontDefault)
        intipLabel.setStyleSheet(self.orange)

        ipintHBLayout.addWidget(intipLabel)

        # ip int value label
        intipValueLabel = QtWidgets.QLabel('192.168.4.5')
        intipValueLabel.setFont(self.fontDefault)
        self.systemWidgets['intip'] = intipValueLabel
        intipValueLabel.setStyleSheet(self.white)

        ipintHBLayout.addWidget(intipValueLabel)

        # Ext Ip
        extipLabel = QtWidgets.QLabel('ext. IP:')
        extipLabel.setFont(self.fontDefault)
        extipLabel.setStyleSheet(self.orange)

        ipintHBLayout.addWidget(extipLabel)

        extipValueLabel = QtWidgets.QLabel('200.154.2.54')
        extipValueLabel.setFont(self.fontDefault)
        self.systemWidgets['extip'] = extipValueLabel
        extipValueLabel.setStyleSheet(self.white)

        ipintHBLayout.addWidget(extipValueLabel)

        verticalLayout.addLayout(ipintHBLayout)
        # -------------------------------------------------
        horizontalLayout = QtWidgets.QHBoxLayout()
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

    def displayDTWeather(self):
        countries = dict(countries_for_language('en'))
        debugRed = 'background-color: rgb(255, 48, 79);'
        timeHeight = 50
        dateHeight = 25
        tempHeight = 60

        timeFont = QtGui.QFont('Fira Code', 45)
        dayFont = QtGui.QFont('Fira Code', 20)
        weekdayFont = QtGui.QFont('Fira Code', 15)
        yearFont = QtGui.QFont('Fira Code', 12)
        monthFont = QtGui.QFont('Fira Code', 12)

        gray = 'color: rgb(143, 143, 143);'

        mainHBLayout = QtWidgets.QHBoxLayout()
        mainHBLayout.setSpacing(0)
        mainHBLayout.setAlignment(QtCore.Qt.AlignHCenter)

        # Horizontal Layout for time
        timeHBLayout = QtWidgets.QHBoxLayout()
        timeHBLayout.setAlignment(QtCore.Qt.AlignHCenter)

        twoPointLabel = [QtWidgets.QLabel(':'), QtWidgets.QLabel(':')]
        for label in twoPointLabel:
            label.setFont(timeFont)
            label.setStyleSheet(gray)
            label.setFixedHeight(timeHeight)

        hourLabel = QtWidgets.QLabel('22')
        hourLabel.setFont(timeFont)
        hourLabel.setStyleSheet(self.white)
        hourLabel.setFixedHeight(timeHeight)
        self.dtwWidgets['hour'] = hourLabel

        minLabel = QtWidgets.QLabel('24')
        minLabel.setFont(timeFont)
        minLabel.setStyleSheet(self.white)
        minLabel.setFixedHeight(timeHeight)
        self.dtwWidgets['min'] = minLabel

        # secLabel = QtWidgets.QLabel('45')
        # secLabel.setFont(timeFont)
        # secLabel.setStyleSheet(self.white)
        # secLabel.setFixedHeight(timeHeight)
        # self.dtwWidgets['sec'] = secLabel

        timeHBLayout.addWidget(hourLabel)
        timeHBLayout.addWidget(twoPointLabel[0])
        timeHBLayout.addWidget(minLabel)
        # timeHBLayout.addWidget(twoPointLabel[1])
        # timeHBLayout.addWidget(secLabel)

        self.dtwWidgets['hour'] = hourLabel
        self.dtwWidgets['min'] = minLabel

        mainHBLayout.addLayout(timeHBLayout)

        # date vertical layout
        dateVBLayout = QtWidgets.QVBoxLayout()
        # date horizontal layout
        dateHBLayout = QtWidgets.QHBoxLayout()
        dateHBLayout.setAlignment(QtCore.Qt.AlignLeft)

        dayLabel = QtWidgets.QLabel('05')
        dayLabel.setFont(dayFont)
        dayLabel.setStyleSheet(self.orange)
        dayLabel.setFixedHeight(dateHeight)

        monthLabel = QtWidgets.QLabel('June')
        monthLabel.setFont(monthFont)
        monthLabel.setStyleSheet(self.white)
        monthLabel.setFixedHeight(dateHeight)
        monthLabel.setAlignment(QtCore.Qt.AlignBottom)

        yearLabel = QtWidgets.QLabel('2020')
        yearLabel.setFont(yearFont)
        yearLabel.setStyleSheet(self.white)
        yearLabel.setFixedHeight(dateHeight)
        yearLabel.setAlignment(QtCore.Qt.AlignBottom)

        dateHBLayout.addWidget(dayLabel)
        dateHBLayout.addWidget(monthLabel)
        dateHBLayout.addWidget(yearLabel)
        self.dtwWidgets['day'] = dayLabel
        self.dtwWidgets['month'] = monthLabel
        self.dtwWidgets['year'] = yearLabel

        dateVBLayout.addLayout(dateHBLayout)

        weekdayHBLayout = QtWidgets.QHBoxLayout()

        weekdayLabel = QtWidgets.QLabel('Saturday')
        weekdayLabel.setFont(weekdayFont)
        weekdayLabel.setStyleSheet(self.white)
        weekdayLabel.setFixedHeight(20)

        weekdayHBLayout.addWidget(weekdayLabel)
        self.dtwWidgets['weekday'] = weekdayLabel

        dateVBLayout.addLayout(weekdayHBLayout)

        mainHBLayout.addLayout(dateVBLayout)

        # --------------------------------------------------------
        # weather conditions

        weatherHBLayout = QtWidgets.QHBoxLayout()

        weatherVBLayout = QtWidgets.QVBoxLayout()
        weatherVBLayout.setAlignment(QtCore.Qt.AlignVCenter)

        tempLabel = QtWidgets.QLabel('22°C')
        tempLabel.setFont(timeFont)
        tempLabel.setStyleSheet(self.white)
        tempLabel.setFixedHeight(tempHeight)
        self.dtwWidgets['temp'] = tempLabel

        weatherHBLayout.addWidget(tempLabel)

        # Cloud Icon
        pixmap = QtGui.QPixmap()

        # pixmap.loadFromData(self.weather.getIcon(weatherData['weather'][0]['icon']))
        cloudIconLabel = QtWidgets.QLabel()
        cloudIconLabel.setPixmap(pixmap)
        cloudIconLabel.setFixedHeight(42)
        cloudIconLabel.setFixedHeight(tempHeight)
        self.dtwWidgets['cloudpixmark'] = cloudIconLabel.pixmap()

        weatherHBLayout.addWidget(cloudIconLabel)
        weatherHBLayout.setAlignment(QtCore.Qt.AlignHCenter)

        cityRegionLabel = QtWidgets.QLabel(
            f"{self.config.getConfig('location')['city']}, {self.config.getConfig('location')['region']}")
        cityRegionLabel.setFont(self.fontDefault)
        cityRegionLabel.setStyleSheet(self.white)

        countryLabel = QtWidgets.QLabel(countries[self.config.getConfig('location')['country']])
        countryLabel.setFont(self.fontDefault)
        countryLabel.setStyleSheet(self.white)

        weatherVBLayout.addWidget(cityRegionLabel)
        weatherVBLayout.addWidget(countryLabel)

        weatherHBLayout.addLayout(weatherVBLayout)
        # ---------------------------------------------------------------------
        # humidity, pressure, visibility,  wind,
        weatherGridLayout = QtWidgets.QGridLayout()

        # humidityIcon
        humidityIcon = QtWidgets.QLabel()
        humidityIcon.setPixmap(QtGui.QPixmap(f'{self.config.resource_path}/images/humidity.png'))
        humidityIcon.setFixedWidth(32)

        pressureIcon = QtWidgets.QLabel()
        pressureIcon.setPixmap(QtGui.QPixmap(f'{self.config.resource_path}/images/pressure.png'))
        pressureIcon.setFixedWidth(32)

        visibilityIcon = QtWidgets.QLabel()
        visibilityIcon.setPixmap(QtGui.QPixmap(f'{self.config.resource_path}/images/visibility.png'))
        visibilityIcon.setFixedWidth(32)

        windIcon = QtWidgets.QLabel()
        windIcon.setPixmap(QtGui.QPixmap(f'{self.config.resource_path}/images/wind.png'))
        windIcon.setFixedWidth(32)

        weatherGridLayout.addWidget(humidityIcon, 0, 0, 1, 1, QtCore.Qt.AlignHCenter)
        weatherGridLayout.addWidget(pressureIcon, 0, 1, 1, 1, QtCore.Qt.AlignHCenter)
        weatherGridLayout.addWidget(visibilityIcon, 0, 2, 1, 1, QtCore.Qt.AlignHCenter)
        weatherGridLayout.addWidget(windIcon, 0, 3, 1, 1, QtCore.Qt.AlignHCenter)
        # ---------------------------------------------------------------------

        humidityLabel = QtWidgets.QLabel('12%')
        humidityLabel.setFont(self.fontDefault)
        humidityLabel.setStyleSheet(self.white)
        self.dtwWidgets['humidity'] = humidityLabel

        pressureLabel = QtWidgets.QLabel('1000hPa')
        pressureLabel.setFont(self.fontDefault)
        pressureLabel.setStyleSheet(self.white)
        self.dtwWidgets['pressure'] = pressureLabel

        visibilityLabel = QtWidgets.QLabel('2Km')
        visibilityLabel.setFont(self.fontDefault)
        visibilityLabel.setStyleSheet(self.white)
        self.dtwWidgets['visibility'] = visibilityLabel

        windLabel = QtWidgets.QLabel('5m/s SE')
        windLabel.setFont(self.fontDefault)
        windLabel.setStyleSheet(self.white)
        self.dtwWidgets['wind'] = windLabel

        weatherGridLayout.addWidget(humidityLabel, 1, 0, 1, 1, QtCore.Qt.AlignHCenter)
        weatherGridLayout.addWidget(pressureLabel, 1, 1, 1, 1, QtCore.Qt.AlignHCenter)
        weatherGridLayout.addWidget(visibilityLabel, 1, 2, 1, 1, QtCore.Qt.AlignHCenter)
        weatherGridLayout.addWidget(windLabel, 1, 3, 1, 1, QtCore.Qt.AlignHCenter)

        self.verticalLayout.addLayout(mainHBLayout)
        self.verticalLayout.addLayout(weatherHBLayout)
        self.verticalLayout.addLayout(weatherGridLayout)
        self.threadweather.updateWeather()

    def displaySystem(self):
        labelDefaultWidth = 80

        systemGroupBox = QtWidgets.QGroupBox('system')
        systemGroupBox.setFont(self.fontGroupBox)
        systemGroupBox.setStyleSheet(self.groupBoxStyle)

        verticalLayout = QtWidgets.QVBoxLayout()

        # distro Label
        distroJson = self.config.getConfig('distro')
        distroStr = f"{distroJson['name']} {distroJson['version']}"
        if not distroJson['codename'] == '':
            distroStr = f"{distroStr} {distroJson['codename']}"

        # ---------------------------------------------------------------------------
        distroHBLayout = QtWidgets.QHBoxLayout()
        distroHBLayout.setAlignment(QtCore.Qt.AlignHCenter)
        distroVBLayout = QtWidgets.QVBoxLayout()

        distroIcon = QtWidgets.QLabel()
        distroIcon.setPixmap(QtGui.QPixmap(distroJson['iconfile']))
        distroIcon.setMinimumSize(QtCore.QSize(32, 32))

        distroHBLayout.addWidget(distroIcon)
        # ---------------------------------------------------------------------------
        # Distro label
        distroLabel = QtWidgets.QLabel(distroStr)
        distroLabel.setFont(self.fontDefault)
        distroLabel.setStyleSheet(self.white)
        # ---------------------------------------------------------------------------
        # kernel label
        platJson = self.config.getConfig('platform')
        kernelLabel = QtWidgets.QLabel(f"Kernel {platJson['release']}")
        kernelLabel.setFont(self.fontDefault)
        kernelLabel.setStyleSheet(self.white)
        # ---------------------------------------------------------------------------
        # Machine Label
        machineLabel = QtWidgets.QLabel(f"node {platJson['node']} arch {platJson['machine']}")
        machineLabel.setFont(self.fontDefault)
        machineLabel.setStyleSheet(self.white)
        # ---------------------------------------------------------------------------
        distroVBLayout.addWidget(distroLabel)
        distroVBLayout.addWidget(kernelLabel)
        distroVBLayout.addWidget(machineLabel)

        distroHBLayout.addLayout(distroVBLayout)

        verticalLayout.addLayout(distroHBLayout)
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
            tempDict = dict()
            tempDict['mountpointValueLabel'] = mountpointValueLabel
            tempDict['totalValueLabel'] = totalValueLabel
            tempDict['usedValueLabel'] = usedValueLabel
            tempDict['usedPB'] = usedPB
            tempDict['freeValueLabel'] = freeValueLabel
            tempDict['freePB'] = freePB
            self.partitionsWidgets.append(tempDict)

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
        for i, msg in enumerate(message):
            self.partitionsWidgets[i]['mountpointValueLabel'].setText(msg['mountpoint'])
            self.partitionsWidgets[i]['totalValueLabel'].setText(msg['total'])
            self.partitionsWidgets[i]['usedValueLabel'].setText(msg['used'])
            self.partitionsWidgets[i]['usedPB'].setValue(msg['percentUsed'])
            self.partitionsWidgets[i]['freeValueLabel'].setText(msg['free'])
            self.partitionsWidgets[i]['freePB'].setValue(msg['percentFree'])

        ipaddrs = self.threadSlow.getIpAddrs()
        self.systemWidgets['intip'].setText(ipaddrs['intip'])
        self.systemWidgets['extip'].setText(ipaddrs['extip'])

    def receiveThreadFastfinish(self, message):

        self.dtwWidgets['hour'].setText(message['hour'])
        self.dtwWidgets['min'].setText(message['min'])
        # self.dtwWidgets['sec'].setText(message['sec'])
        self.dtwWidgets['day'].setText(f"{message['day']},")
        self.dtwWidgets['month'].setText(f" {message['month']} ")
        self.dtwWidgets['year'].setText(message['year'])
        self.dtwWidgets['weekday'].setText(message['weekday'])
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

    def receiveThreadWeatherFinish(self, message):
        self.dtwWidgets['temp'].setText(message['temp'])
        self.dtwWidgets['humidity'].setText(message['humidity'])
        self.dtwWidgets['pressure'].setText(message['pressure'])
        self.dtwWidgets['visibility'].setText(message['visibility'])
        self.dtwWidgets['wind'].setText(message['wind'])
