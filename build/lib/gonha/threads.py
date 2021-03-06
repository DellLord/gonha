from PyQt5 import QtCore, QtGui
from gonha.util import Config
import psutil
import time
import humanfriendly
from gonha.util import VirtualMachine
from gonha.util import Nvidia
from datetime import datetime
from gonha.util import Weather
from gonha.util import Smart
from unit_convert import UnitConvert
import portolan


class ThreadNvidia(QtCore.QThread):
    nvidia = Nvidia()
    signal = QtCore.pyqtSignal(list, name='ThreadNvidiaFinish')

    def __init__(self, parent=None):
        super(ThreadNvidia, self).__init__(parent)
        self.finished.connect(self.updateNvidia)

    def updateNvidia(self):
        gpuMessage = self.nvidia.getDeviceHealth()
        self.signal.emit(gpuMessage)
        self.start()

    def run(self):
        self.sleep(2)  # sleep for 2 sec


class ThreadWeather(QtCore.QThread):
    signal = QtCore.pyqtSignal(dict, name='ThreadWeatherFinish')
    weather = Weather()
    config = Config()

    def __init__(self, parent=None):
        super(ThreadWeather, self).__init__(parent)
        self.finished.connect(self.updateWeather)

    def updateWeather(self):
        tempType = self.config.getConfig('temptype')
        message = dict()
        if self.config.isOnline():
            try:
                data = self.weather.getData()
                scale = 'C'
                temp = float(data['main']['temp'])
                if tempType == 'Kelvin':
                    temp = self.config.convertToKelvin(temp)
                    scale = 'K'
                elif tempType == 'Fahrenheit':
                    temp = self.config.convertToFahrenheit(temp)
                    scale = 'F'

                # tempInteger = int(data['main']['temp'])
                message['temp'] = temp
                message['scale'] = scale
                message['humidity'] = f"{data['main']['humidity']}%"
                message['pressure'] = f"{data['main']['pressure']}hPa"
                visibilityAsKm = UnitConvert(metres=int(data['visibility'])).kilometres
                message['visibility'] = f"{visibilityAsKm}Km"
                windDir = portolan.abbr(float(data['wind']['deg']))
                message['wind'] = f"{data['wind']['speed']}m/s {windDir}"
                pixmap = QtGui.QPixmap()
                data = self.weather.getIcon(data['weather'][0]['icon'])
                pixmap.loadFromData(data)
                message['icon'] = pixmap
            except Exception as e:
                self.weather.printException(e)
                message.update({'temp': '', 'humidity': '', 'pressure': '', 'visibility': '', 'wind': ''})

            self.signal.emit(message)

        self.start()

    def run(self):
        self.sleep(1800)  # sleep 30 minutes


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
        if self.config.isOnline():
            counter1 = psutil.net_io_counters(pernic=True)[self.iface]
            time.sleep(1)
            counter2 = psutil.net_io_counters(pernic=True)[self.iface]
            downSpeed = counter2.bytes_recv - counter1.bytes_recv
            upSpeed = counter2.bytes_sent - counter1.bytes_sent
            # get io statistics since boot
            net_io = psutil.net_io_counters(pernic=True)
            self.signal.emit(
                {
                    'downSpeed': downSpeed,
                    'upSpeed': upSpeed,
                    'iface': self.iface,
                    'bytesSent': net_io[self.iface].bytes_sent,
                    'bytesRcv': net_io[self.iface].bytes_recv
                }
            )


class ThreadSlow(QtCore.QThread):
    signal = QtCore.pyqtSignal(list, name='ThreadSlowFinish')

    def __init__(self, parent=None):
        super(ThreadSlow, self).__init__(parent)
        self.finished.connect(self.threadFinished)
        self.config = Config()

    def threadFinished(self):
        self.start()

    def getIpAddrs(self):
        if self.config.isOnline():
            ipDict = dict()
            ipDict['extip'] = self.config.getExtIp()
            ipDict['intip'] = self.config.getIntIp()
            ipDict['gw'] = self.config.getGw()
            return ipDict

    def getPartitions(self):
        msg = list()
        for mntPoint in self.config.getConfig('filesystems'):
            disk_usage = psutil.disk_usage(mntPoint)
            tempDict = dict()
            tempDict['mountpoint'] = mntPoint
            tempDict['total'] = '{}'.format(humanfriendly.format_size(disk_usage.total))
            tempDict['used'] = '{}'.format(humanfriendly.format_size(disk_usage.used))
            tempDict['free'] = '{}'.format(humanfriendly.format_size(disk_usage.free))
            tempDict['percentUsed'] = disk_usage.percent
            tempDict['percentFree'] = 100 - int(disk_usage.percent)
            msg.append(tempDict)

        return msg

    def run(self):
        time.sleep(10)
        self.signal.emit(self.getPartitions())


class ThreadFast(QtCore.QThread):
    signal = QtCore.pyqtSignal(dict, name='ThreadFastFinish')
    message = dict()
    smart = Smart()
    config = Config()
    tempType = config.getConfig('temptype')

    def __init__(self, parent=None):
        super(ThreadFast, self).__init__(parent)
        self.finished.connect(self.threadFinished)

    def threadFinished(self):
        self.start()

    def getUpTime(self):
        return self.config.getUptime()

    def run(self):
        now = datetime.now()
        self.message['hour'] = now.strftime('%H')

        self.message['min'] = now.strftime('%M')
        self.message['sec'] = now.strftime('%S')

        self.message['date'] = now.strftime("%A, %d %B %Y")

        self.message['day'] = now.strftime('%d')
        self.message['weekday'] = now.strftime('%A')
        self.message['month'] = now.strftime('%B')
        self.message['year'] = now.strftime('%Y')

        cpuFreq = psutil.cpu_freq()
        ram = psutil.virtual_memory()
        swap = psutil.swap_memory()

        self.message['cpufreq'] = '{:.0f}'.format(cpuFreq.current)
        self.message['cpufreqMax'] = '{:.0f}'.format(cpuFreq.max)
        self.message['ramused'] = '{}'.format(humanfriendly.format_size(ram.used))
        self.message['ramTotal'] = '{}'.format(humanfriendly.format_size(ram.total))
        self.message['swapused'] = '{}'.format(humanfriendly.format_size(swap.used))
        self.message['swapTotal'] = '{}'.format(humanfriendly.format_size(swap.total))
        self.message['cpuProgressBar'] = psutil.cpu_percent()
        self.message['ramProgressBar'] = ram.percent
        self.message['swapProgressBar'] = swap.percent
        self.message['boottime'] = self.getUpTime()

        # --------------------------------------------------------
        # if inside virtual machine , so bypass sensor
        if not VirtualMachine().getStatus():
            tempConfig = self.config.getConfig('cputemp')
            sensors = psutil.sensors_temperatures()
            for i, sensor in enumerate(sensors):
                if i == tempConfig['index']:
                    for shwtemp in sensors[sensor]:
                        if shwtemp.label == tempConfig['label']:
                            current = shwtemp.current
                            high = shwtemp.high
                            critical = shwtemp.critical
                            if high is None:
                                high = 75.0  # 75 celsius for high temp cpu

                            if critical is None:
                                critical = 90.0  # 90 celsius for critical temp cpu

                            current, high, critical, scale = self.config.normalizeTemps(current, high, critical)

                            self.message['label'] = shwtemp.label
                            self.message['current'] = current
                            self.message['high'] = high
                            self.message['critical'] = critical
                            self.message['scale'] = '{}'.format(scale)
                            break
        else:
            self.message['label'] = 'vmTdie'
            self.message['current'] = 50.0
            self.message['high'] = 70.0
            self.message['critical'] = 90.0
            self.message['scale'] = 'C'

        # Storages
        devices = self.smart.getDevicesHealth()
        self.message['devices'] = list()
        for d in devices:
            tempDict = dict()
            tempDict['device'] = d['device']
            tempDict['model'] = d['model']
            tempDict['temp'] = d['temp']
            tempDict['high'] = d['high']
            tempDict['critical'] = d['critical']
            self.message['devices'].append(tempDict)

        time.sleep(1)
        self.signal.emit(self.message)
