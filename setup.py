import setuptools
import re
import os
import shutil

currentDir = os.getcwd()
distDir = f'{currentDir}/dist'
buildDir = f'{currentDir}/build'

if os.path.isdir(distDir):
    shutil.rmtree(distDir)

if os.path.isdir(buildDir):
    shutil.rmtree(buildDir)

with open("README.md", "r") as fh:
    long_description = fh.read()

pattern = "([0-9]+.[0-9]+.[0-9]+)"
utilFile = 'gonha/util.py'
version = ''
with open(utilFile, 'r') as f:
    for line in f.readlines():
        searchObj = re.search(pattern, line)
        if searchObj:
            version = searchObj.group()
            break

setuptools.setup(
    name="gonha",
    version=version,
    author="Fred Cox",
    author_email="fredcox@gmail.com",
    description="Light-weight system monitor for Linux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fredcox/gonha",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires='>=3.8',
    scripts=['bin/gonha'],

    install_requires=[
        'PyQt5',
        'ewmh',
        'psutil',
        'humanfriendly',
        'pathlib',
        'PyInquirer',
        'colr',
        'distro',
        'py-cpuinfo',
        'requests',
        'netifaces',
        'country_list',
        'portolan',
        'unit-convert',
        'gputil'
    ],
    include_package_data=True,
    zip_safe=False,
)
