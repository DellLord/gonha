import os
from pathlib import Path
from colr import color
from PyInquirer import prompt
import psutil
import json
import sys
from cpuinfo import get_cpu_info
import distro
import platform
import requests
import subprocess
import netifaces
from telnetlib import Telnet
import socket
import urllib.request
import numpy as np
import GPUtil


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
        # ----------------------------------------------------------------
        # disks config
        diskList = list()
        self.updateConfig({'storages': diskList})
        # ----------------------------------------------------------------
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
        print(color('Starting Wizard...', fore=14))
        print('')

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
                    'name': 'gpus',
                    'message': 'Select the Nvidia GPU you want to display',
                    'choices': gpuChoices,
                }
            ]

            gpuResponse = prompt(gpuQuestions)
            self.updateConfig(gpuResponse)

        if not self.isOnline():
            print(color('Error: ', fore=11), color('[ ', fore=14), color('you are offline', fore=9),
                  color(' ]', fore=14))
            sys.exit(1)

        print(color('retrieving info about your geolocalization : ', fore=11))
        geoData = self.getWeatherData()
        print(color('Next...', fore=10))
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
            sensors = psutil.sensors_temperatures()
            tempUserChoices = []
            for i, key in enumerate(sensors):
                tempUserChoices.append(
                    '{} - [{}] current temp: {:.0f}°C'.format(i, key, float(sensors[key][0].current))
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

    @staticmethod
    def getVersion():
        return '1.3.0'

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

    @staticmethod
    def isOnline():
        try:
            socket.create_connection(("8.8.8.8", 53))
            return True
        except OSError:
            return False


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
        print(color('Error! ', fore=11), color('[ ', fore=14), e, color('Error! ', fore=9), color(' ]', fore=14))


class Smart:
    vm = VirtualMachine()

    def getDevicesHealth(self):
        message = list()
        if not self.vm.getStatus():
            message.append({'device': '/dev/vmsda', 'model': 'VIRTUAL SSD', 'temp': '38', 'scale': 'C'})
        else:
            # Append fake data to virtual machine
            message.append({'device': '/dev/vmsda', 'model': 'VIRTUAL SSD', 'temp': '38', 'scale': 'C'})

        return message
