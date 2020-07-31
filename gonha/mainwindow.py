import sys
from PyQt5 import QtWidgets
from ewmh import EWMH
from gonha.threads import *
from gonha.util import Weather
from gonha.util import Smart
from gonha.util import Nvidia
from country_list import countries_for_language
import logging
import coloredlogs

logger = logging.getLogger(__name__)
coloredlogs.install()


class Alert(QtWidgets.QDialog):

    def __init__(self, message):
        super(Alert, self).__init__()

        self.setWindowTitle("Gonha - [ Alert ]")

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)

        messageLabel = QtWidgets.QLabel(message)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(messageLabel)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class MainWindow(QtWidgets.QMainWindow):
    config = Config()
    iface = config.getConfig('iface')
    version = config.getVersion()
    app = QtWidgets.QApplication(sys.argv)
    threadNetworkStats = ThreadNetworkStats()
    threadNvidia = ThreadNvidia()
    threadFast = ThreadFast()
    threadSlow = ThreadSlow()
    threadweather = ThreadWeather()
    partitionsWidgets = []
    upDownRateWidgets = []
    diskWidgets = []
    dtwWidgets = dict()
    systemWidgets = dict()
    nvidiaWidgets = list()
    verticalLayout = QtWidgets.QVBoxLayout()
    weather = Weather()
    debugRed = 'background-color: rgb(255, 48, 79);'
    nvidia = Nvidia()
    smart = Smart()
    pbDefaultHeight = 20

    def __init__(self):
        super(MainWindow, self).__init__()
        logger.info(f':: Gonha - {self.version} ::')
        logger.info('Starting...')
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
        self.threadNvidia.signal.connect(self.receiveThreadNvidia)
        centralWidGet = QtWidgets.QWidget(self)
        centralWidGet.setLayout(self.verticalLayout)
        self.setCentralWidget(centralWidGet)
        # -----------------------------------------------------------------------------------------------
        # before show main window, check all dependencies and refuse if any thing wrong
        self.checkDependencies()
        #
        self.show()
        # Show in all workspaces
        self.ew = EWMH()
        self.all_wins = self.ew.getClientList()
        self.wins = filter(lambda wHandle: wHandle.get_wm_class()[1] == 'gonha', self.all_wins)
        for w in self.wins:
            self.ew.setWmDesktop(w, 0xffffffff)

        self.ew.display.flush()

        self.threadFast.start()
        self.threadSlow.start()
        self.threadNetworkStats.start()

        self.loadPosition()
        self.displayDTWeather()
        self.displaySystem()
        if self.nvidia.getStatus():
            self.displayNvidia()

        self.displayIface()
        self.displayPartitions()

    def checkDependencies(self):
        # ------------------------------------------------------------------------
        # Check if user need update config file
        oldVersion = self.config.getConfig('version')
        if self.config.getVersion() != oldVersion:
            dialog = Alert('You need run "gonha --config" on terminal')
            dialog.exec_()
            sys.exit()
        # ------------------------------------------------------------------------
        # Check if user have privileged sudo without password
        if not self.smart.checkSmartCtlStatus():
            dialog = Alert(
                'You need enable smartmontools to run without sudo. Please read the README.md (install instructions)')
            dialog.exec_()
            sys.exit()

        if not self.smart.checkNvmeCliStatus():
            dialog = Alert(
                'You need enable nvme-cli to run without sudo. Please read the README.md (install instructions)')
            dialog.exec_()
            sys.exit()

    def getDefaultGb(self, title):
        defaultGb = QtWidgets.QGroupBox(title)
        defaultGb.setFont(self.fontGroupBox)
        defaultGb.setStyleSheet(self.groupBoxStyle)
        return defaultGb

    def displayNvidia(self):
        gpuMessage = self.nvidia.getDeviceHealth()

        nvidiaGroupBox = self.getDefaultGb('nvidia')
        verticalLayout = QtWidgets.QVBoxLayout()
        # ---------------------------------------------------
        # nvidia data
        nvidiaHBLayout = QtWidgets.QHBoxLayout()

        nvidiaLabel = QtWidgets.QLabel()
        nvidiaLabel.setPixmap(QtGui.QPixmap(f"{self.config.resource_path}/images/nvidia.png"))
        nvidiaLabel.setFixedWidth(64)
        nvidiaHBLayout.addWidget(nvidiaLabel)

        infoVLayout = QtWidgets.QVBoxLayout()
        infoVLayout.setSpacing(0)
        infoVLayout.setAlignment(QtCore.Qt.AlignVCenter)
        for gpu in gpuMessage:
            tempDict = dict()
            infoHLayout = QtWidgets.QHBoxLayout()

            nameLabel = QtWidgets.QLabel(gpu['name'])
            tempDict['name'] = nameLabel
            nameLabel.setFixedWidth(240)
            nameLabel.setAlignment(QtCore.Qt.AlignLeft)
            self.setLabel(nameLabel, self.white, self.fontDefault)
            infoHLayout.addWidget(nameLabel)

            loadLabel = QtWidgets.QLabel('load:')
            loadLabel.setAlignment(QtCore.Qt.AlignRight)
            self.setLabel(loadLabel, self.orange, self.fontDefault)
            infoHLayout.addWidget(loadLabel)

            loadValueLabel = QtWidgets.QLabel(f"{gpu['load']}%")
            tempDict['load'] = loadValueLabel
            loadValueLabel.setAlignment(QtCore.Qt.AlignRight)
            self.setLabel(loadValueLabel, self.white, self.fontDefault)
            infoHLayout.addWidget(loadValueLabel)

            infoVLayout.addLayout(infoHLayout)

            mtempHLayout = QtWidgets.QHBoxLayout()

            memoryLabel = QtWidgets.QLabel('memory:')
            memoryLabel.setFixedWidth(70)
            self.setLabel(memoryLabel, self.orange, self.fontDefault)
            mtempHLayout.addWidget(memoryLabel)

            usedTotalMemLabel = QtWidgets.QLabel(f"{gpu['memoryUsed']}MB/{gpu['memoryTotal']}MB")
            tempDict['usedTotalMemory'] = usedTotalMemLabel
            self.setLabel(usedTotalMemLabel, self.white, self.fontDefault)
            mtempHLayout.addWidget(usedTotalMemLabel)

            tempIcon = QtWidgets.QLabel()
            tempIcon.setPixmap(QtGui.QPixmap(f'{self.config.resource_path}/images/temp.png'))
            tempIcon.setFixedHeight(24)
            tempIcon.setFixedWidth(24)
            mtempHLayout.addWidget(tempIcon)

            tempLabel = QtWidgets.QLabel(f"{gpu['temp']}°C")
            tempDict['temp'] = tempLabel
            self.setLabel(tempLabel, self.white, self.fontDefault)
            tempLabel.setAlignment(QtCore.Qt.AlignRight)
            tempLabel.setFixedWidth(70)
            mtempHLayout.addWidget(tempLabel)

            infoVLayout.addLayout(mtempHLayout)
            self.nvidiaWidgets.append(tempDict)

        nvidiaHBLayout.addLayout(infoVLayout)
        verticalLayout.addLayout(nvidiaHBLayout)

        nvidiaGroupBox.setLayout(verticalLayout)
        self.verticalLayout.addWidget(nvidiaGroupBox)
        self.threadNvidia.start()

    def displayIface(self):
        ifaceGroupBox = self.getDefaultGb('net')
        verticalLayout = QtWidgets.QVBoxLayout()
        # ---------------------------------------------------
        # Ip int Label
        ipintHBLayout = QtWidgets.QHBoxLayout()

        intipLabel = QtWidgets.QLabel('int. IP:')
        self.setLabel(intipLabel, self.orange, self.fontDefault)

        ipintHBLayout.addWidget(intipLabel)

        # ip int value label
        intipValueLabel = QtWidgets.QLabel('')
        self.setLabel(intipValueLabel, self.white, self.fontDefault)
        self.systemWidgets['intip'] = intipValueLabel

        ipintHBLayout.addWidget(intipValueLabel)

        # Ext Ip
        extipLabel = QtWidgets.QLabel('ext. IP:')
        self.setLabel(extipLabel, self.orange, self.fontDefault)

        ipintHBLayout.addWidget(extipLabel)

        extipValueLabel = QtWidgets.QLabel('')
        self.setLabel(extipValueLabel, self.white, self.fontDefault)
        self.systemWidgets['extip'] = extipValueLabel

        ipintHBLayout.addWidget(extipValueLabel)

        verticalLayout.addLayout(ipintHBLayout)
        # -------------------------------------------------
        horizontalLayout = QtWidgets.QHBoxLayout()

        netCardIcon = QtWidgets.QLabel()
        netCardIcon.setPixmap(QtGui.QPixmap(f"{self.config.resource_path}/images/netcard.png"))
        netCardIcon.setFixedSize(24, 24)
        horizontalLayout.addWidget(netCardIcon)

        # -------------------------------------------------
        # ifaceValueLabel
        ifaceValueLabel = QtWidgets.QLabel('')
        self.setLabel(ifaceValueLabel, self.white, self.fontDefault)
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
        ifaceDownRateLabel = QtWidgets.QLabel('')
        self.setLabel(ifaceDownRateLabel, self.white, self.fontDefault)
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
        ifaceUpRateLabel = QtWidgets.QLabel('')
        self.setLabel(ifaceUpRateLabel, self.white, self.fontDefault)
        ifaceUpRateLabel.setAlignment(QtCore.Qt.AlignRight)
        ifaceUpRateLabel.setFixedWidth(110)
        self.upDownRateWidgets.append(ifaceUpRateLabel)
        horizontalLayout.addWidget(ifaceUpRateLabel)

        verticalLayout.addLayout(horizontalLayout)
        # ---------------------------------------------------

        # Total in
        bytesSentRcvHLayout = QtWidgets.QHBoxLayout()

        bytesRcvLabel = QtWidgets.QLabel('total in:')
        self.setLabel(bytesRcvLabel, self.orange, self.fontDefault)
        bytesSentRcvHLayout.addWidget(bytesRcvLabel)

        bytesRcvValueLabel = QtWidgets.QLabel('')
        self.setLabel(bytesRcvValueLabel, self.white, self.fontDefault)
        bytesRcvValueLabel.setAlignment(QtCore.Qt.AlignRight)
        self.upDownRateWidgets.append(bytesRcvValueLabel)
        bytesSentRcvHLayout.addWidget(bytesRcvValueLabel)

        # Total out
        bytesSentLabel = QtWidgets.QLabel('total out:')
        self.setLabel(bytesSentLabel, self.orange, self.fontDefault)
        bytesSentRcvHLayout.addWidget(bytesSentLabel)

        bytesSentValueLabel = QtWidgets.QLabel('')
        self.setLabel(bytesSentValueLabel, self.white, self.fontDefault)
        bytesSentValueLabel.setAlignment(QtCore.Qt.AlignRight)
        self.upDownRateWidgets.append(bytesSentValueLabel)
        bytesSentRcvHLayout.addWidget(bytesSentValueLabel)

        verticalLayout.addLayout(bytesSentRcvHLayout)

        ifaceGroupBox.setLayout(verticalLayout)
        self.verticalLayout.addWidget(ifaceGroupBox)

    def displayDTWeather(self):
        countries = dict(countries_for_language('en'))
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
        self.setLabel(hourLabel, self.white, timeFont)
        hourLabel.setFixedHeight(timeHeight)
        self.dtwWidgets['hour'] = hourLabel

        minLabel = QtWidgets.QLabel('24')
        self.setLabel(minLabel, self.white, timeFont)
        minLabel.setFixedHeight(timeHeight)
        self.dtwWidgets['min'] = minLabel

        timeHBLayout.addWidget(hourLabel)
        timeHBLayout.addWidget(twoPointLabel[0])
        timeHBLayout.addWidget(minLabel)

        self.dtwWidgets['hour'] = hourLabel
        self.dtwWidgets['min'] = minLabel

        mainHBLayout.addLayout(timeHBLayout)

        # date vertical layout
        dateVBLayout = QtWidgets.QVBoxLayout()
        # date horizontal layout
        dateHBLayout = QtWidgets.QHBoxLayout()
        dateHBLayout.setAlignment(QtCore.Qt.AlignLeft)

        dayLabel = QtWidgets.QLabel('05')
        self.setLabel(dayLabel, self.orange, dayFont)
        dayLabel.setFixedHeight(dateHeight)

        monthLabel = QtWidgets.QLabel('June')
        self.setLabel(monthLabel, self.white, monthFont)
        monthLabel.setFixedHeight(dateHeight)
        monthLabel.setAlignment(QtCore.Qt.AlignBottom)

        yearLabel = QtWidgets.QLabel('2020')
        yearLabel.setFont(yearFont)
        yearLabel.setStyleSheet(self.white)
        self.setLabel(yearLabel, self.white, yearFont)
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
        self.setLabel(weekdayLabel, self.white, weekdayFont)
        weekdayLabel.setFixedHeight(20)

        weekdayHBLayout.addWidget(weekdayLabel)
        self.dtwWidgets['weekday'] = weekdayLabel

        dateVBLayout.addLayout(weekdayHBLayout)

        mainHBLayout.addLayout(dateVBLayout)

        # --------------------------------------------------------
        # weather conditions

        weatherHBLayout = QtWidgets.QHBoxLayout()

        weatherVBLayout = QtWidgets.QVBoxLayout()
        weatherVBLayout.setSpacing(0)
        weatherVBLayout.setAlignment(QtCore.Qt.AlignVCenter)

        tempLabel = QtWidgets.QLabel('')
        self.setLabel(tempLabel, self.white, timeFont)
        tempLabel.setFixedHeight(tempHeight)
        self.dtwWidgets['temp'] = tempLabel

        weatherHBLayout.addWidget(tempLabel)

        # Cloud Icon
        cloudIconLabel = QtWidgets.QLabel()
        cloudIconLabel.setFixedHeight(42)
        cloudIconLabel.setFixedHeight(tempHeight)
        self.dtwWidgets['cloudicon'] = cloudIconLabel

        weatherHBLayout.addWidget(cloudIconLabel)
        weatherHBLayout.setAlignment(QtCore.Qt.AlignHCenter)

        cityRegionLabel = QtWidgets.QLabel(
            f"{self.config.getConfig('location')['city']}")
        self.setLabel(cityRegionLabel, self.white, self.fontDefault)

        countryLabel = QtWidgets.QLabel(countries[self.config.getConfig('location')['country']])
        self.setLabel(countryLabel, self.white, self.fontDefault)

        weatherVBLayout.addWidget(cityRegionLabel)
        weatherVBLayout.addWidget(countryLabel)

        weatherHBLayout.addLayout(weatherVBLayout)
        # ---------------------------------------------------------------------
        # humidity, pressure, visibility,  wind,
        weatherGridLayout = QtWidgets.QGridLayout()
        weatherGridLayout.setSpacing(0)

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

        humidityLabel = QtWidgets.QLabel('')
        self.setLabel(humidityLabel, self.white, self.fontDefault)
        self.dtwWidgets['humidity'] = humidityLabel

        pressureLabel = QtWidgets.QLabel('')
        self.setLabel(pressureLabel, self.white, self.fontDefault)
        self.dtwWidgets['pressure'] = pressureLabel

        visibilityLabel = QtWidgets.QLabel('')
        self.setLabel(visibilityLabel, self.white, self.fontDefault)
        self.dtwWidgets['visibility'] = visibilityLabel

        windLabel = QtWidgets.QLabel('')
        self.setLabel(windLabel, self.white, self.fontDefault)
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
        labelDefaultHeight = 15
        labelDefaultAlignment = QtCore.Qt.AlignRight
        pbDefaultWidth = 180
        systemGroupBox = self.getDefaultGb('system')

        verticalLayout = QtWidgets.QVBoxLayout()
        verticalLayout.setSpacing(0)

        # distro Label
        distroJson = self.config.getConfig('distro')
        distroStr = f"{distroJson['name']} {distroJson['version']}"
        if not distroJson['codename'] == '':
            distroStr = f"{distroStr} {distroJson['codename']}"

        # ---------------------------------------------------------------------------
        distroHBLayout = QtWidgets.QHBoxLayout()
        distroHBLayout.setAlignment(QtCore.Qt.AlignHCenter)
        distroVBLayout = QtWidgets.QVBoxLayout()
        distroVBLayout.setSpacing(0)

        distroIcon = QtWidgets.QLabel()
        distroIcon.setPixmap(QtGui.QPixmap(distroJson['iconfile']))
        distroIcon.setFixedHeight(64)

        distroHBLayout.addWidget(distroIcon)
        # ---------------------------------------------------------------------------
        # Distro label
        distroLabel = QtWidgets.QLabel(distroStr)
        self.setLabel(distroLabel, self.white, self.fontDefault)
        distroLabel.setFixedHeight(labelDefaultHeight)
        # ---------------------------------------------------------------------------
        # kernel label
        platJson = self.config.getConfig('platform')
        kernelLabel = QtWidgets.QLabel(f"Kernel {platJson['release']}")
        self.setLabel(kernelLabel, self.white, self.fontDefault)
        kernelLabel.setFixedHeight(labelDefaultHeight)
        # ---------------------------------------------------------------------------
        # Machine Label
        machineLabel = QtWidgets.QLabel(f"node {platJson['node']} arch {platJson['machine']}")
        self.setLabel(machineLabel, self.white, self.fontDefault)
        machineLabel.setFixedHeight(labelDefaultHeight)
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
        self.setLabel(bootTimeValueLabel, self.white, self.fontDefault)
        self.systemWidgets['boottime'] = bootTimeValueLabel

        bootTimeValueLabel.setAlignment(QtCore.Qt.AlignCenter)

        bootTimeHboxLayout.addWidget(bootTimeValueLabel)

        verticalLayout.addLayout(bootTimeHboxLayout)
        # ---------------------------------------------------------------------------
        cpuHBLayout = QtWidgets.QHBoxLayout()

        cpuBrandLabel = QtWidgets.QLabel(self.config.getConfig('cpuinfo'))
        self.setLabel(cpuBrandLabel, self.white, self.fontDefault)
        cpuBrandLabel.setAlignment(QtCore.Qt.AlignHCenter)
        cpuHBLayout.addWidget(cpuBrandLabel)

        verticalLayout.addLayout(cpuHBLayout)

        # Cpu load
        cpuLoadHBLayout = QtWidgets.QHBoxLayout()

        cpuIcon = QtWidgets.QLabel()
        cpuIcon.setPixmap(QtGui.QPixmap(f"{self.config.resource_path}/images/cpu.png"))
        cpuIcon.setFixedSize(labelDefaultWidth, 24)
        cpuLoadHBLayout.addWidget(cpuIcon)

        cpuProgressBar = QtWidgets.QProgressBar()
        cpuProgressBar.setFixedHeight(self.pbDefaultHeight)
        cpuProgressBar.setFixedWidth(pbDefaultWidth)
        cpuProgressBar.setFont(self.fontDefault)
        cpuProgressBar.setStyleSheet(self.greenPBStyle)
        cpuProgressBar.setValue(12)
        self.systemWidgets['cpuProgressBar'] = cpuProgressBar

        cpuLoadHBLayout.addWidget(cpuProgressBar)

        cpuFreqLabel = QtWidgets.QLabel('14343.34 Mhz')
        cpuFreqLabel.setAlignment(labelDefaultAlignment)
        self.setLabel(cpuFreqLabel, self.white, self.fontDefault)
        self.systemWidgets['cpufreq'] = cpuFreqLabel

        cpuLoadHBLayout.addWidget(cpuFreqLabel)

        verticalLayout.addLayout(cpuLoadHBLayout)

        # ---------------------------------------------------------------------------
        # ram load
        ramLoadHBLayout = QtWidgets.QHBoxLayout()

        ramIcon = QtWidgets.QLabel()
        ramIcon.setPixmap(QtGui.QPixmap(f"{self.config.resource_path}/images/ram.png"))
        ramIcon.setFixedSize(labelDefaultWidth, 24)
        ramLoadHBLayout.addWidget(ramIcon)

        ramProgressBar = QtWidgets.QProgressBar()
        ramProgressBar.setFixedHeight(self.pbDefaultHeight)
        ramProgressBar.setFixedWidth(pbDefaultWidth)
        ramProgressBar.setFont(self.fontDefault)
        ramProgressBar.setStyleSheet(self.greenPBStyle)
        self.systemWidgets['ramProgressBar'] = ramProgressBar
        ramProgressBar.setValue(32)

        ramLoadHBLayout.addWidget(ramProgressBar)

        ramUsedLabel = QtWidgets.QLabel('15443 MB')
        ramUsedLabel.setAlignment(labelDefaultAlignment)
        self.setLabel(ramUsedLabel, self.white, self.fontDefault)
        self.systemWidgets['ramused'] = ramUsedLabel

        ramLoadHBLayout.addWidget(ramUsedLabel)

        verticalLayout.addLayout(ramLoadHBLayout)
        # ---------------------------------------------------------------------------
        # swap load
        swapHBLayout = QtWidgets.QHBoxLayout()

        swapIcon = QtWidgets.QLabel()
        swapIcon.setPixmap(QtGui.QPixmap(f"{self.config.resource_path}/images/swap.png"))
        swapIcon.setFixedSize(labelDefaultWidth, 24)

        swapHBLayout.addWidget(swapIcon)

        swapProgressBar = QtWidgets.QProgressBar()
        swapProgressBar.setFixedHeight(self.pbDefaultHeight)
        swapProgressBar.setFixedWidth(pbDefaultWidth)
        swapProgressBar.setFont(self.fontDefault)
        swapProgressBar.setStyleSheet(self.greenPBStyle)
        self.systemWidgets['swapProgressBar'] = swapProgressBar
        swapProgressBar.setValue(52)

        swapHBLayout.addWidget(swapProgressBar)

        swapUsedLabel = QtWidgets.QLabel('16654 MB')
        swapUsedLabel.setAlignment(labelDefaultAlignment)
        self.setLabel(swapUsedLabel, self.white, self.fontDefault)
        self.systemWidgets['swapused'] = swapUsedLabel

        swapHBLayout.addWidget(swapUsedLabel)

        verticalLayout.addLayout(swapHBLayout)

        # ---------------------------------------------------------------------------
        # Temperature
        tempHBLayout = QtWidgets.QHBoxLayout()
        tempHBLayout.setAlignment(QtCore.Qt.AlignHCenter)
        tempHBLayout.setSpacing(5)

        tempIcon = QtWidgets.QLabel()
        tempIcon.setPixmap(QtGui.QPixmap(f'{self.config.resource_path}/images/temp.png'))
        tempIcon.setFixedHeight(24)
        tempIcon.setFixedWidth(24)

        tempLabel = QtWidgets.QLabel('label:')
        # tempLabel.setFixedWidth(labelDefaultWidth)
        self.setLabel(tempLabel, self.orange, self.fontDefault)

        tempHBLayout.addWidget(tempIcon)
        tempHBLayout.addWidget(tempLabel)

        tempValueLabel = QtWidgets.QLabel('label')
        self.systemWidgets['label'] = tempValueLabel
        self.setLabel(tempValueLabel, self.white, self.fontDefault)

        tempHBLayout.addWidget(tempValueLabel)

        tempCurrentLabel = QtWidgets.QLabel('current:')
        self.setLabel(tempCurrentLabel, self.orange, self.fontDefault)

        tempHBLayout.addWidget(tempCurrentLabel)

        tempCurrentValueLabel = QtWidgets.QLabel('30C')
        self.setLabel(tempCurrentValueLabel, self.white, self.fontDefault)
        self.systemWidgets['current'] = tempCurrentValueLabel

        tempHBLayout.addWidget(tempCurrentValueLabel)

        verticalLayout.addLayout(tempHBLayout)

        # ---------------------------------------------------------------------------
        systemGroupBox.setLayout(verticalLayout)
        self.verticalLayout.addWidget(systemGroupBox)

    def displayPartitions(self):
        mntPoints = self.threadSlow.getPartitions()
        diskGroupBox = self.getDefaultGb('disks')
        verticalLayout = QtWidgets.QVBoxLayout()
        verticalLayout.setSpacing(0)
        verticalLayout.setAlignment(QtCore.Qt.AlignTop)
        pbFixedWidth = 260
        labelAlignment = QtCore.Qt.AlignRight
        labelDefaultWidth = 80

        # Devices Health
        devices = self.smart.getDevicesHealth()
        for i, d in enumerate(devices):
            deviceHBLayout = QtWidgets.QHBoxLayout()

            ssdIcon = QtWidgets.QLabel()
            ssdIcon.setPixmap(QtGui.QPixmap(f'{self.config.resource_path}/images/ssd.png'))
            ssdIcon.setFixedSize(20, 20)
            deviceHBLayout.addWidget(ssdIcon)

            deviceLabel = QtWidgets.QLabel(d['device'])
            deviceLabel.setFixedWidth(120)
            self.setLabel(deviceLabel, self.white, self.fontDefault)
            deviceHBLayout.addWidget(deviceLabel)

            deviceModelLabel = QtWidgets.QLabel(d['model'])
            deviceModelLabel.setFixedWidth(220)
            self.setLabel(deviceModelLabel, self.white, self.fontDefault)
            deviceHBLayout.addWidget(deviceModelLabel)

            tempIcon = QtWidgets.QLabel()
            tempIcon.setPixmap(QtGui.QPixmap(f'{self.config.resource_path}/images/temp.png'))
            tempIcon.setFixedHeight(20)
            tempIcon.setFixedWidth(20)
            deviceHBLayout.addWidget(tempIcon)

            deviceTempLabel = QtWidgets.QLabel(f"{d['temp']}")
            self.setLabel(deviceTempLabel, self.white, self.fontDefault)
            deviceHBLayout.addWidget(deviceTempLabel)

            deviceScaleLabel = QtWidgets.QLabel(f"°{d['scale']}")

            self.diskWidgets.append(
                {'device': deviceLabel, 'model': deviceModelLabel, 'temp': deviceTempLabel, 'scale': deviceScaleLabel})

            verticalLayout.addLayout(deviceHBLayout)

        for mntPoint in mntPoints:
            mountpointHorizontalLayout = QtWidgets.QHBoxLayout()

            # ------------- mountpoint ----------------------
            mountpointValueLabel = QtWidgets.QLabel(mntPoint['mountpoint'])
            self.setLabel(mountpointValueLabel, self.white, self.fontDefault)
            mountpointHorizontalLayout.addWidget(mountpointValueLabel)

            totalValueLabel = QtWidgets.QLabel(mntPoint['total'])
            self.setLabel(totalValueLabel, self.white, self.fontDefault)
            totalValueLabel.setAlignment(QtCore.Qt.AlignRight)
            mountpointHorizontalLayout.addWidget(totalValueLabel)

            verticalLayout.addLayout(mountpointHorizontalLayout)
            # ----------------------------------------------------------
            # used stats
            usedHorizontalLayout = QtWidgets.QHBoxLayout()
            usedLabel = QtWidgets.QLabel('used:')
            self.setLabel(usedLabel, self.orange, self.fontDefault)
            usedLabel.setFixedWidth(labelDefaultWidth)
            usedHorizontalLayout.addWidget(usedLabel)

            # ProgressBar
            usedPB = QtWidgets.QProgressBar()
            usedPB.setFixedHeight(self.pbDefaultHeight)
            usedPB.setFont(self.fontDefault)
            usedPB.setStyleSheet(self.redPBStyle)
            usedPB.setFixedWidth(pbFixedWidth)
            usedPB.setValue(mntPoint['percentUsed'])

            usedHorizontalLayout.addWidget(usedPB)

            usedValueLabel = QtWidgets.QLabel(mntPoint['used'])
            self.setLabel(usedValueLabel, self.white, self.fontDefault)
            usedValueLabel.setAlignment(labelAlignment)

            usedHorizontalLayout.addWidget(usedValueLabel)

            verticalLayout.addLayout(usedHorizontalLayout)
            # ----------------------------------------------------------
            # free stats
            freeHorizontalLayout = QtWidgets.QHBoxLayout()
            freeLabel = QtWidgets.QLabel('free:')
            self.setLabel(freeLabel, self.orange, self.fontDefault)
            freeLabel.setFixedWidth(labelDefaultWidth)
            freeHorizontalLayout.addWidget(freeLabel)

            freePB = QtWidgets.QProgressBar()
            freePB.setFixedHeight(self.pbDefaultHeight)
            freePB.setFont(self.fontDefault)
            freePB.setStyleSheet(self.greenPBStyle)
            freePB.setFixedWidth(pbFixedWidth)
            freePB.setAlignment(QtCore.Qt.AlignLeft)
            freePB.setValue(mntPoint['percentFree'])

            freeHorizontalLayout.addWidget(freePB)

            freeValueLabel = QtWidgets.QLabel(mntPoint['free'])
            self.setLabel(freeValueLabel, self.white, self.fontDefault)
            freeValueLabel.setAlignment(labelAlignment)
            freeHorizontalLayout.addWidget(freeValueLabel)

            verticalLayout.addLayout(freeHorizontalLayout)

            # ----------------------------------------------------------

            tempDict = dict()
            tempDict['mountpointValueLabel'] = mountpointValueLabel
            tempDict['totalValueLabel'] = totalValueLabel
            tempDict['usedValueLabel'] = usedValueLabel
            tempDict['usedPB'] = usedPB
            tempDict['freeValueLabel'] = freeValueLabel
            tempDict['freePB'] = freePB
            self.partitionsWidgets.append(tempDict)

        diskGroupBox.setLayout(verticalLayout)
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
        logger.info('Screen: {}'.format(screen.name()))
        size = screen.size()
        logger.info('Screen Resolution: {} x {}'.format(size.width(), size.height()))
        rect = screen.availableGeometry()
        logger.info('Available space for gonha: {} x {}'.format(rect.width(), rect.height()))
        # move window to top right
        win = self.geometry()
        self.move(rect.width() - win.width(), 0)

    def receiveThreadSlowFinish(self, message):
        for i, msg in enumerate(message):
            self.partitionsWidgets[i]['mountpointValueLabel'].setText(msg['mountpoint'])
            self.partitionsWidgets[i]['totalValueLabel'].setText(msg['total'])
            self.partitionsWidgets[i]['usedValueLabel'].setText(msg['used'])
            self.partitionsWidgets[i]['usedPB'].setValue(msg['percentUsed'])
            self.partitionsWidgets[i]['freeValueLabel'].setText(msg['free'])
            self.partitionsWidgets[i]['freePB'].setValue(msg['percentFree'])

        if self.config.isOnline():
            ipaddrs = self.threadSlow.getIpAddrs()
            self.systemWidgets['intip'].setText(ipaddrs['intip'])
            self.systemWidgets['extip'].setText(ipaddrs['extip'])

    def receiveThreadFastfinish(self, message):

        self.dtwWidgets['hour'].setText(message['hour'])
        self.dtwWidgets['min'].setText(message['min'])
        # self.dtwWidgets['sec'].setText(message['sec'])
        self.dtwWidgets['day'].setText(f"{message['day']}")
        self.dtwWidgets['month'].setText(f", {message['month']} ")
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

        self.systemWidgets['cpufreq'].setText(f"{message['cpufreq']}/{message['cpufreqMax']} Mhz")
        self.systemWidgets['ramused'].setText(f"{message['ramused']}/{message['ramTotal']}")
        self.systemWidgets['swapused'].setText(f"{message['swapused']}/{message['swapTotal']}")

        self.systemWidgets['boottime'].setText(message['boottime'])

        current = int(''.join(filter(str.isdigit, message['current'])))
        self.analizeTemp(self.systemWidgets['current'], float(current), 85)

        for i, d in enumerate(message['devices']):
            self.diskWidgets[i]['device'].setText(d['device'])
            self.diskWidgets[i]['model'].setText(d['model'])
            self.diskWidgets[i]['temp'].setText(f"{d['temp']}°C")
            maxtemp = 73.0
            self.analizeTemp(self.diskWidgets[i]['device'], float(d['temp']), maxtemp)
            self.analizeTemp(self.diskWidgets[i]['temp'], float(d['temp']), maxtemp)

    def receiveThreadWeatherFinish(self, message):
        # logger.info(message)
        self.dtwWidgets['temp'].setText(message['temp'])
        self.dtwWidgets['humidity'].setText(message['humidity'])
        self.dtwWidgets['pressure'].setText(message['pressure'])
        self.dtwWidgets['visibility'].setText(message['visibility'])
        self.dtwWidgets['wind'].setText(message['wind'])
        self.dtwWidgets['cloudicon'].setPixmap(message['icon'])

    @staticmethod
    def setLabel(label, labelcolor, font):
        label.setFont(font)
        label.setStyleSheet(labelcolor)

    def receiveThreadNetworkStats(self, message):
        self.upDownRateWidgets[0].setText(message['iface'])
        self.upDownRateWidgets[1].setText('{}/s'.format(humanfriendly.format_size(message['downSpeed'])))
        self.upDownRateWidgets[2].setText('{}/s'.format(humanfriendly.format_size(message['upSpeed'])))
        self.upDownRateWidgets[3].setText(humanfriendly.format_size(message['bytesRcv']))
        self.upDownRateWidgets[4].setText(humanfriendly.format_size(message['bytesSent']))

    def receiveThreadNvidia(self, message):
        for msg in message:
            # get the id
            idx = int(msg['id'])
            self.nvidiaWidgets[idx]['name'].setText(msg['name'])
            self.nvidiaWidgets[idx]['load'].setText(f"{str(msg['load'])}%")
            self.nvidiaWidgets[idx]['usedTotalMemory'].setText(f"{msg['memoryUsed']}MB/{msg['memoryTotal']}MB")
            self.nvidiaWidgets[idx]['temp'].setText(f"{msg['temp']}°C")
            maxtemp = 80.0
            self.analizeTemp(self.nvidiaWidgets[idx]['temp'], float(msg['temp']), maxtemp)

    @staticmethod
    def analizeTemp(label, current, maxValue):
        colorNormal = 'color: rgb(157, 255, 96);'
        colorWarning = 'color: rgb(255, 255, 153);'
        colorAlarm = 'color: rgb(255, 79, 79);'
        percent30 = maxValue - (maxValue * 0.3)
        percent10 = maxValue - (maxValue * 0.1)
        label.setStyleSheet(colorNormal)
        if current >= percent10:
            label.setStyleSheet(colorAlarm)
        elif current >= percent30:
            label.setStyleSheet(colorWarning)
