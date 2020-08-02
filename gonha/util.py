import os
from pathlib import Path
from PyInquirer import prompt
import psutil
import json
import sys
from cpuinfo import get_cpu_info
import distro
import requests
import subprocess
import netifaces
import urllib.request
import coloredlogs
import logging
from telnetlib import Telnet
import numpy as np
import socket
import platform
import re
import time

os.environ['QT_LOGGING_RULES'] = "qt5ct.debug=false"
logger = logging.getLogger(__name__)
coloredlogs.install()


class Nvidia:
    smiCommand = 'nvidia-smi'
    # , nounits
    smiSuffixCommand = '--format=csv,noheader'
    smiStatus = subprocess.getstatusoutput(smiCommand)[0]
    nvidiaEntity = dict()

    def __init__(self):
        if self.getSmiStatus():
            count, DriverVersion = self.getOutputCommand('count,driver_version')
            self.nvidiaEntity.update(
                {
                    'count': int(count),
                    'driver_version': DriverVersion,
                    'gpus': self.getGPUsInfo()
                }
            )

    def getGPUsInfo(self):
        numGPUS = int(self.getOutputCommand('count')[0])
        message = list()
        for id in range(numGPUS):
            tempDict = dict()
            gpu_uuid, gpu_name, display_mode, vbios_version, fan_speed, pstate, memory_total, memory_used, memory_free, temperature_gpu, power_management, power_draw, clocks_current_graphics, clocks_current_sm, clocks_current_memory, clocks_current_video, utilization_gpu = self.getOutputCommand(
                'gpu_uuid,gpu_name,display_mode,vbios_version,fan.speed,pstate,memory.total,memory.used,memory.free,temperature.gpu,power.management,power.draw,clocks.current.graphics,clocks.current.sm,clocks.current.memory,clocks.current.video,utilization.gpu'
            )

            tempDict.update({
                'id': id,
                'gpu_uuid': gpu_uuid,
                'gpu_name': gpu_name,
                'display_mode': display_mode,
                'vbios_version': vbios_version,
                'fan_speed': fan_speed,
                'pstate': pstate,
                'memory_total': memory_total,
                'memory_used': memory_used,
                'memory_free': memory_free,
                'temperature_gpu': float(temperature_gpu),
                'temperature_gpu_high': 70.0,
                'temperature_gpu_critical': 85.0,  # 40% above
                'temperature_scale': 'C',
                'power_management': power_management,
                'power_draw': power_draw,
                'clocks_current_graphics': clocks_current_graphics,
                'clocks_current_sm': clocks_current_sm,
                'clocks_current_memory': clocks_current_memory,
                'clocks_current_video': clocks_current_video,
                'utilization_gpu': utilization_gpu
            })
            message.append(tempDict)

        return message

    def getOutputCommand(self, queryList):
        return subprocess.getoutput(f"{self.smiCommand} --id=0 --query-gpu={queryList} {self.smiSuffixCommand}").split(',')

    def getSmiStatus(self):
        if self.smiStatus == 0:
            return True
        else:
            return False


class VirtualMachine:
    @staticmethod
    def getStatus():
        outCmd = subprocess.getoutput('systemd-detect-virt')
        if outCmd == 'none':
            return False
        else:
            return True


class Config:
    resource_path = os.path.dirname(__file__)
    distrosDir = f'{resource_path}/images/distros'
    cfgFile = f'{Path.home()}/.config/gonha/config.json'
    globalJSON = dict()
    apiKey = 'at_cY0kTF6KP8LuMrXidniTMnkOa7XTE'
    url = 'https://ip-geolocation.whoisxmlapi.com/api/v1'
    myExtIp = subprocess.getoutput('curl -s ifconfig.me')
    outJson = {'city': None, 'region': None, 'country': None}
    nvidia = Nvidia()

    def __init__(self):
        self.version = self.getVersion()
        if not os.path.isfile(self.cfgFile):
            self.wizard()

    def wizard(self):
        # check if config file exists
        if os.path.isfile(self.cfgFile):
            os.remove(self.cfgFile)
        # ----------------------------------------------------------------
        # Get cpu info
        cpuInfo = get_cpu_info()
        # ----------------------------------------------------------------
        # update with current version
        self.updateConfig({'version': self.getVersion()})

        # get Platform especific details
        plat = platform.uname()
        self.updateConfig({
            'platform': {
                'system': plat.system,
                'node': plat.node,
                'release': plat.release,
                'machine': plat.machine
            }
        })
        # ----------------------------------------------------------------
        # update with distro information
        dist = {
            'distro': {
                'id': distro.id(),
                'name': distro.name(),
                'codename': distro.codename(),
                'version': distro.version(),
                'iconfile': f'{self.distrosDir}/{distro.id()}.png'
            }
        }
        self.updateConfig(dist)
        # ----------------------------------------------------------------
        logger.info('Starting Wizard...')
        # ----------------------------------------
        # temperature format Question
        tempTypeQuestions = [
            {
                'type': 'list',
                'name': 'temptype',
                'message': 'Do you want see temperatures in Kelvin, Fahrenheit or Celsius?',
                'choices': [
                    'Kelvin',
                    'Fahrenheit',
                    'Celsius'
                ],
            }
        ]
        psutil.sensors_temperatures('kelvin')
        tempTypeResponse = prompt(tempTypeQuestions)
        self.updateConfig(tempTypeResponse)

        # ----------------------------------------------------------------
        # Check if nvmes exists
        nvme = self.getNvmes()
        if len(nvme) >= 1:
            # -----------------------------------------------------------------------------------------------------
            nvmeChoices = list()
            nvmeChoices.append({
                'name': 'device: [{}] [/dev/{}]'.format(nvme[0]['id'], nvme[0]['name']),
                'value': nvme[0]['name']
            })

            nvmeQuestions = [
                {
                    'type': 'checkbox',
                    'name': 'nvme',
                    'message': 'Hummm, You have M.2 NVMe´s, please choose the correct device do you want monitoring:',
                    'choices': nvmeChoices,
                }
            ]
            nvmeResponse = prompt(nvmeQuestions)
            self.updateConfig(nvmeResponse)
        else:
            self.updateConfig({'nvme': list()})

        # ---------------------------------------------------------------
        # GPuDialog
        # gpus = GPUtil.getGPUs()
        if self.nvidia.nvidiaEntity['count'] > 0:
            gpuChoices = []
            # Filesystem sections
            for gpu in self.nvidia.nvidiaEntity['gpus']:
                gpuChoices.append(
                    {
                        'name': 'id: [{}] model [{}] uuid: [{}]'.format(gpu['id'], gpu['gpu_name'], gpu['gpu_uuid']),
                        'value': gpu['gpu_uuid']
                    }
                )

            gpuQuestions = [
                {
                    'type': 'checkbox',
                    'name': 'nvidia',
                    'message': 'Select the Nvidia GPU you want to display',
                    'choices': gpuChoices,
                }
            ]

            gpuResponse = prompt(gpuQuestions)
            self.updateConfig(gpuResponse)

        if not self.isOnline():
            logger.info('Error: you are offline')
            sys.exit(1)

        logger.info('retrieving info about your geolocalization : ')
        geoData = self.getWeatherData()
        logger.info('Next...')
        geoQuestions = [
            {
                'type': 'input',
                'name': 'city',
                'message': 'What\'s your city name',
                'default': geoData['city']
            },
            {
                'type': 'input',
                'name': 'region',
                'message': 'What\'s your region',
                'default': geoData['region']
            },
            {
                'type': 'input',
                'name': 'country',
                'message': 'What\'s your country code',
                'default': geoData['country']
            }
        ]

        geoResponse = prompt(geoQuestions)
        self.updateConfig({'location': geoResponse})
        # ----------------------------------------
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
        # -------------------------------------------------------------------------
        # Cpu Info
        self.updateConfig({'cpuinfo': cpuInfo['brand_raw']})

        # -------------------------------------------------------------------------
        # if Inside virtual machine, so bypass
        if not VirtualMachine().getStatus():
            # Temperature Question
            cpuSensors = psutil.sensors_temperatures()
            tempUserChoices = []
            for index, sensor in enumerate(cpuSensors):
                for shwtemp in cpuSensors[sensor]:
                    tempUserChoices.append({
                        'name': '{} - [{}] current temp: {:.0f}°C'.format(index, shwtemp.label, shwtemp.current),
                        'value': {'index': index, 'label': shwtemp.label}
                    })

            tempQuestions = [
                {
                    'type': 'list',
                    'name': 'cputemp',
                    'message': 'What is your CPU temperature sensor?',
                    'choices': tempUserChoices,
                }
            ]
            tempResponse = prompt(tempQuestions)
            self.updateConfig(tempResponse)
        # -----------------------------------------------------------------------------------------------------
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
        # -----------------------------------------------------------------------------------------------------

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
        # logger.info(self.globalJSON)
        self.writeConfig()

        logger.info('That´s OK')
        logger.info('Now, you can running gonha command again with all config options for your system!')
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

    @staticmethod
    def getVersion():
        return '1.6.14'

    def getExtIp(self):
        return self.myExtIp

    def getIntIp(self):
        eth = netifaces.ifaddresses(self.getConfig('iface'))
        return eth[netifaces.AF_INET][0]['addr']

    @staticmethod
    def getGw():
        gws = netifaces.gateways()
        return gws['default'][netifaces.AF_INET][0]

    @staticmethod
    def convertToFahrenheit(temp):
        return (temp * 1.8) + 32

    @staticmethod
    def convertToKelvin(temp):
        return 273.15 + temp

    def normalizeTemps(self, current, high, critical):
        tempConfig = self.getConfig('temptype')
        retCurrent = current
        retHigh = high
        retCritical = critical
        retScale = 'C'
        if tempConfig == 'Kelvin':
            retCurrent = self.convertToKelvin(current)
            retHigh = self.convertToKelvin(high)
            retCritical = self.convertToKelvin(critical)
            retScale = 'K'
        elif tempConfig == 'Fahrenheit':
            retCurrent = self.convertToFahrenheit(current)
            retHigh = self.convertToFahrenheit(high)
            retCritical = self.convertToFahrenheit(critical)
            retScale = 'F'

        return retCurrent, retHigh, retCritical, retScale

    def getWeatherData(self):
        response = requests.get(f"{self.url}?apiKey={self.apiKey}&ipAddress={self.myExtIp}")

        if response.status_code == 200:
            self.outJson.clear()
            tempJson = json.loads(response.text)
            self.outJson.update(
                {
                    'city': tempJson['location']['city'],
                    'region': tempJson['location']['region'],
                    'country': tempJson['location']['country'],
                    'lat': tempJson['location']['lat'],
                    'lng': tempJson['location']['lng']

                }
            )

        return self.outJson

    # Check for nvmes
    @staticmethod
    def getNvmes():
        nvmesJson = json.loads(subprocess.getoutput('lsblk --json'))
        nvmesRet = list()
        for i, nvme in enumerate(nvmesJson['blockdevices']):
            if 'nvme' in nvme['name']:
                tempDict = dict()
                tempDict['id'] = i
                tempDict['name'] = nvme['name']
                nvmesRet.append(tempDict)

        return nvmesRet

    @staticmethod
    def isOnline():
        try:
            socket.create_connection(("8.8.8.8", 53))
            return True
        except OSError:
            return False

    @staticmethod
    def getKernelInfo():
        kernelPattern = "([0-9].[0-9].[0-9]+)"
        kernelString = platform.platform()
        kernelString = re.search(kernelPattern, kernelString).group(0)
        kernelList = kernelString.split('.')
        kernelDict = dict()
        kernelDict.update({'kernelVersion': int(kernelList[0]), 'majorRevision': int(kernelList[1]),
                           'minorRevision': int(kernelList[2])})
        return kernelDict

    @staticmethod
    def getUptime():
        bootTime = time.time() - psutil.boot_time()
        day = bootTime // (24 * 3600)
        bootTime = bootTime % (24 * 3600)
        hour = bootTime // 3600
        bootTime %= 3600
        minutes = bootTime // 60
        bootTime %= 60
        seconds = bootTime
        return f'up {int(day)} days, {int(hour)} hours {int(minutes)} minutes and {int(seconds)} seconds'


class Weather:
    config = Config()
    city = config.getConfig('location')['city']
    url = 'http://api.openweathermap.org/data/2.5/weather?q='
    apikey = 'e943e3d03143693768df6ca7c621c8b5'
    iconUrlPrefix = 'https://openweathermap.org/img/wn/'
    iconUrlSuffix = '@2x.png'

    def getData(self):
        try:
            res = requests.get(f'{self.url}{self.city}&APPID={self.apikey}&units=metric')
            return res.json()
        except Exception as e:
            self.printException(e)

    def getIcon(self, iconStr):
        if self.config.isOnline():
            with urllib.request.urlopen(f"{self.iconUrlPrefix}{iconStr}{self.iconUrlSuffix}") as response:
                return response.read()

    @staticmethod
    def printException(e):
        logger.info(f'Error! {e}')


class Smart:
    host = '127.0.0.1'
    port = 7634
    vm = VirtualMachine()
    model = str()
    temp = 0
    message = list()
    storageType = 'sata'
    config = Config()
    temperature = {
        'format': 'Celsius',
        'scale': 'C',
        'current': 0.0,
        'high': 0.0,
        'critical': 0.0
    }

    def __init__(self):
        self.analizeScale()

    def hddtempIsOk(self):
        try:
            socket.create_connection((self.host, self.port))
            return True
        except OSError:
            return False

    def analizeScale(self):
        tempType = self.config.getConfig('temptype')
        if tempType == 'Kelvin':
            self.temperature['format'] = 'Kelvin'
            self.temperature['scale'] = 'K'
        elif tempType == 'Fahrenheit':
            self.temperature['format'] = 'Fahrenheit'
            self.temperature['scale'] = 'F'

    def uniFormTempValues(self, current, high, critical):
        self.temperature['current'] = current
        self.temperature['high'] = high
        self.temperature['critical'] = critical
        if self.temperature['scale'] == 'K':
            self.temperature['current'] = self.config.convertToKelvin(current)
            self.temperature['high'] = self.config.convertToKelvin(high)
            self.temperature['critical'] = self.config.convertToKelvin(critical)

        if self.temperature['scale'] == 'F':
            self.temperature['current'] = self.config.convertToFahrenheit(current)
            self.temperature['high'] = self.config.convertToFahrenheit(high)
            self.temperature['critical'] = self.config.convertToFahrenheit(critical)

    def getDevicesHealth(self):
        self.message.clear()
        self.message = self.getHddTemp()
        devices = self.config.getConfig('nvme')
        if len(devices) >= 1:
            sensors = psutil.sensors_temperatures()
            for sensor in sensors:
                if 'nvme' in sensor:
                    current = sensors[sensor][0].current
                    high = sensors[sensor][0].high
                    if high is None:
                        high = 70.0

                    critical = sensors[sensor][0].critical
                    if critical is None:
                        critical = 82.0

                    self.uniFormTempValues(current, high, critical)

                    self.model = sensors[sensor][0].label
                    self.message.append({
                        'device': '/dev/{}'.format(devices[0]),
                        'model': '{}'.format(devices[0]),
                        'temp': self.temperature['current'],
                        'scale': self.temperature['scale'],
                        'high': self.temperature['high'],
                        'critical': self.temperature['critical'],
                    })

        return self.message

    def getHddTemp(self):
        message = list()
        if self.hddtempIsOk():
            if not self.vm.getStatus():
                with Telnet(self.host, self.port) as tn:
                    lines = tn.read_all().decode('utf-8')

                if lines != '':
                    data = lines
                    # remove first char
                    data = data[1:]
                    # remove the last char
                    data = ''.join([data[i] for i in range(len(data)) if i != len(data) - 1])
                    # replace double || by one |
                    data = data.replace('||', '|')
                    # convert to array
                    data = data.split('|')
                    dataLen = len(data)
                    forLenght = int(dataLen / 4)
                    newarray = np.array_split(data, forLenght)
                    for na in newarray:
                        current = float(na[2])
                        high = current + (current * 0.3)
                        critical = current + (current * 0.4)

                        self.uniFormTempValues(current, high, critical)

                        message.append({
                            'device': na[0],
                            'model': na[1],
                            'temp': self.temperature['current'],
                            'scale': self.temperature['scale'],
                            'high': self.temperature['high'],
                            'critical': self.temperature['critical'],
                        })

            else:
                # Append fake data to virtual machine
                message.append(
                    {
                        'device': '/dev/vmsda',
                        'model': 'VIRTUAL SSD',
                        'temp': 38.0,
                        'high': 70.0,
                        'critical': 80.0,
                        'scale': 'C'
                    }
                )

            return message
