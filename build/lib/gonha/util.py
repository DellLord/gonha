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
import GPUtil
import coloredlogs
import logging
from telnetlib import Telnet
import numpy as np
import socket
import platform
import re

logger = logging.getLogger(__name__)
coloredlogs.install()


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
        # ----------------------------------------------------------------
        # Check if nvmes exists
        nvmes = self.getNvmes()
        if len(nvmes) >= 1:
            # -----------------------------------------------------------------------------------------------------
            nvmesChoices = []
            # Filesystem sections
            for nvme in nvmes:
                nvmesChoices.append(
                    {
                        'name': 'device: [{}] [/dev/{}]'.format(nvme['id'], nvme['name']),
                        'value': nvme['name']
                    }
                )

            nvmesQuestions = [
                {
                    'type': 'checkbox',
                    'name': 'nvmes',
                    'message': 'You have M.2 NVMe´s, please choose the correct device do you want monitoring:',
                    'choices': nvmesChoices,
                }
            ]
            nvmesResponse = prompt(nvmesQuestions)
            logger.info(nvmesResponse)
        else:
            nvmesResponse = list()
        # ----------------------------------------------------------------
        # update config with available nvme list
        self.updateConfig({'nvmes': nvmesResponse})
        # ----------------------------------------------------------------

        # GPuDialog
        gpus = GPUtil.getGPUs()
        if len(gpus) > 0:
            gpuChoices = []
            # Filesystem sections
            for gpu in gpus:
                gpuChoices.append(
                    {
                        'name': '{}'.format(gpu.name),
                        'value': gpu.id
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
            for i, key in enumerate(cpuSensors):
                if not ('nvme' in key):
                    tempUserChoices.append(
                        '{} - [{}] current temp: {:.0f}°C'.format(i, key, float(cpuSensors[key][0].current))
                    )

            # Temperature Questions
            tempQuestions = [
                {
                    'type': 'list',
                    'name': 'temp',
                    'message': 'What is your CPU temperature sensor?',
                    'choices': tempUserChoices,
                    'filter': lambda val: tempUserChoices.index(val)
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
        return '1.6.0'

    def getExtIp(self):
        return self.myExtIp

    def getIntIp(self):
        eth = netifaces.ifaddresses(self.getConfig('iface'))
        return eth[netifaces.AF_INET][0]['addr']

    @staticmethod
    def getGw():
        gws = netifaces.gateways()
        return gws['default'][netifaces.AF_INET][0]

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


class Nvidia:
    config = Config()

    def getStatus(self):
        try:
            devices = self.config.getConfig('nvidia')
            if len(devices) >= 1:
                return True
        except Exception as e:
            logger.info(f'No {e} gpu card found in your system.')

        return False

    def getDeviceHealth(self):
        gpus = GPUtil.getGPUs()
        idxs = self.config.getConfig('nvidia')
        message = []
        for idx in idxs:
            for gpu in gpus:
                tempDict = dict()
                if idx == gpu.id:
                    tempDict.update({
                        'id': gpu.id,
                        'name': gpu.name,
                        'load': gpu.load,
                        'freeMemory': gpu.memoryFree,
                        'memoryUsed': gpu.memoryUsed,
                        'memoryTotal': gpu.memoryTotal,
                        'temp': gpu.temperature
                    })
                    message.append(tempDict)

        return message


class Smart:
    host = '127.0.0.1'
    port = 7634
    vm = VirtualMachine()
    model = str()
    temp = 0
    message = list()
    storageType = 'sata'
    config = Config()

    def hddtempIsOk(self):
        try:
            socket.create_connection((self.host, self.port))
            return True
        except OSError:
            return False

    def getDevicesHealth(self):
        self.message.clear()
        self.message = self.getHddTemp()
        devices = self.config.getConfig('nvmes')
        if len(devices) >= 1:
            sensors = psutil.sensors_temperatures()
            for sensor in sensors:
                if 'nvme' in sensor:
                    self.model = sensors[sensor][0].label
                    self.temp = sensors[sensor][0].current
                    self.message.append({
                        'device': devices['nvmes'][0],
                        'model': self.model,
                        'temp': self.temp,
                        'scale': 'C'
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
                        message.append({'device': na[0], 'model': na[1], 'temp': na[2], 'scale': na[3]})

            else:
                # Append fake data to virtual machine
                message.append({'device': '/dev/vmsda', 'model': 'VIRTUAL SSD', 'temp': '38', 'scale': 'C'})

            return message
