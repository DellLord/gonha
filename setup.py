import setuptools
import re

with open("README.md", "r") as fh:
    long_description = fh.read()

# update aboutdialog.ui with correct version
version = '0.2.8'
pattern = "([0-9]+.[0-9]+.[0-9]+)"
newlines = []
dialog_filename = 'gonha/mainwindow.ui'
with open(dialog_filename, 'r') as f:
    for line in f.readlines():
        if re.search(pattern, line):
            newlines.append(re.sub(pattern, version, line))
        else:
            newlines.append(line)

with open(dialog_filename, 'w') as f:
    for line in newlines:
        f.write(line)


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
        'distro'
    ],
    include_package_data=True,
    zip_safe=False,
)
