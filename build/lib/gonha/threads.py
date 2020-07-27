from PyQt5 import QtCore
from gonha.util import Config
import psutil
import time
import humanfriendly
from gonha.util import VirtualMachine
from datetime import datetime
import random


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

    def getPartitions(self):
        msg = []
        for mntPoint in self.config.getConfig('filesystems'):
            disk_usage = psutil.disk_usage(mntPoint)
            msg.append({
                'mountpoint': mntPoint,
                'total': '{}'.format(humanfriendly.format_size(disk_usage.total)),
                'used': '{}'.format(humanfriendly.format_size(disk_usage.used)),
                'free': '{}'.format(humanfriendly.format_size(disk_usage.free)),
                'percentUsed': disk_usage.percent,
                'percentFree': 100 - int(disk_usage.percent)
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

    @staticmethod
    def getUpTime():
        timedelta = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        timedeltaInSeconds = timedelta.days * 24 * 3600 + timedelta.seconds
        minutes, seconds = divmod(timedeltaInSeconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        return f'{days} days, {hours} hrs {minutes} min and {seconds} sec'

    def run(self):
        now = datetime.now()
        dateFormat = self.config.getConfig('dateFormat')
        if dateFormat == '24 hours':
            self.message['hour'] = now.strftime('%H')
            self.message['ampm'] = ''
        else:
            self.message['hour'] = now.strftime('%I')
            self.message['ampm'] = now.strftime('%p')

        self.message['min'] = now.strftime('%M')
        self.message['sec'] = now.strftime('%S')
        self.message['date'] = now.strftime("%A, %d %B %Y")

        self.message['cpufreq'] = '{:.0f} Mhz'.format(psutil.cpu_freq().current)
        self.message['ramused'] = '{}'.format(humanfriendly.format_size(psutil.virtual_memory().used))
        self.message['swapused'] = '{}'.format(humanfriendly.format_size(psutil.swap_memory().used))
        self.message['cpuProgressBar'] = psutil.cpu_percent()
        self.message['ramProgressBar'] = psutil.virtual_memory().percent
        self.message['swapProgressBar'] = psutil.swap_memory().percent
        self.message['boottime'] = self.getUpTime()

        # --------------------------------------------------------
        # if inside virtual machine , so bypass sensor
        if not VirtualMachine().getStatus():
            sensorIndex = int(self.config.getConfig('temp'))
            sensors = psutil.sensors_temperatures()
            for i, key in enumerate(sensors):
                if i == sensorIndex:
                    self.message['label'] = sensors[key][0].label
                    self.message['current'] = '{:.0f}°C'.format(float(sensors[key][0].current))
                    break
        else:
            self.message['label'] = 'vmtemp'
            self.message['current'] = '{:.0f}°C'.format(random.uniform(1, 100))

        time.sleep(1)
        self.signal.emit(self.message)
