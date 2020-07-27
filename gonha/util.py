import subprocess
import os
from pathlib import Path
from colr import color
from PyInquirer import prompt
import psutil
import json
import sys
from cpuinfo import get_cpu_info


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
    mainWindowFile = f'{resource_path}/mainwindow.ui'
    cfgFile = f'{Path.home()}/.config/gonha/config.json'
    globalJSON = dict()

    def __init__(self):
        self.version = self.getVersion()

        if not os.path.isfile(self.cfgFile):
            self.wizard()

    def wizard(self):
        cpuInfo = get_cpu_info()
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
        # -------------------------------------------------------------------------
        # Cpu Info
        self.updateConfig({'cpuinfo': cpuInfo['brand_raw']})
        print(self.globalJSON)
        # -------------------------------------------------------------------------
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
        return '1.0.4'

