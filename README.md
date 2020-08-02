[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![PyPI version](https://badge.fury.io/py/gonha.svg)](https://badge.fury.io/py/gonha)
[![GitHub issues](https://img.shields.io/github/issues/fredcox/gonha)](https://github.com/fredcox/gonha/issues)
[![GitHub forks](https://img.shields.io/github/forks/fredcox/gonha)](https://github.com/fredcox/gonha/network)
[![GitHub stars](https://img.shields.io/github/stars/fredcox/gonha)](https://github.com/fredcox/gonha/stargazers)
[![GitHub license](https://img.shields.io/github/license/fredcox/gonha)](https://github.com/fredcox/gonha/blob/master/LICENSE)


# Gonha :art: 

![Gonha - Logo](https://raw.githubusercontent.com/fredcox/gonha/master/gonha/images/logo.png)



Contributors

* [About](#about)
* [Dependencies](#dependencies)
* [Install](#install)
* [How to Upgrade](#howtoupgrade)
* [Screenshot](#screenshot)
* [Contributors](#contributors)
* [License](#license)
* [Buy me a Coffee](#buy-me-a-coffee)

## About

![Gonha - Logo](https://raw.githubusercontent.com/fredcox/gonha/master/gonha/images/shot.png)

***Gonha*** is a simple light-weight system monitor for Linux

## Dependencies

1. FullHD Display 1920 x 1080 pixels.
2. Linux Kernel >= 5.5.x :: **Kernel Version >= 5 and Major Revision >= 5** is **required** to running this application 
3. Pyhton 3.8 or later
4. python3-devel 
5. Fira Code Font
6. curl >=7.68 
7. hddtemp >=0.3 :: you need run hddtemp as daemon on your system. Install ***hddtemp***, edit the file ***/etc/default/hddtemp*** and 
change the line ***RUN_DAEMON="false"*** to ***RUN_DAEMON="true"***. Gonha will connect with hddtemp default port ***7634***, please ***don´t change*** 
the default port number config param. 

 ### Installing Fira Code Font

```bash
$ wget https://github.com/tonsky/FiraCode/releases/download/5.2/Fira_Code_v5.2.zip
$ unzip Fira_Code_v5.2.zip -d Fira_Code
$ cd Fira_Code/
$ cp ttf/* ~/.local/share/fonts/
$ fc-cache -v
```

## Install

Now, after install the font you can install gonha! :)
Remember, ***$HOME/.local/bin*** must be in included in your PATH variable!

```bash
$ pip3 install gonha --user
$ gonha
```

In your window manager (Kde, Cinammon, Gnome, Mate, Xfce) settings for startup application specify delay minimun
of ***5 seconds***, this is necessary for ***gonha*** become visible in all workspaces.

See the example above in Cinammon Startup Applications Settings

![Gonha - Startup Applications](https://raw.githubusercontent.com/fredcox/gonha/master/gonha/images/startupdelay.png)



### Fedora 32 Requirements

To install gonha in **Fedora 32** you need specify **--user** in the pip3 command:

```bash
$ sudo dnf install python3-devel
```
And install the python3-devel dependence.  

```bash
$ sudo dnf install python3-devel
```

### Ubuntu, PopOS or MxLinux Requirements

```bash
$ sudo apt install libxcb-xinerama0
```

## How to Upgrade

To upgrade gonha run the following command in the terminal:

```bash
$ pip3 install gonha --upgrade
```


## Screenshot

### Linux Mint 20 

![Linux Mint - Screenshot](https://raw.githubusercontent.com/fredcox/gonha/master/gonha/images/gonhascreenshot.png)

## Contributors

This project exists thanks to all the people who contribute!

1. [Fred Lins](https://github.com/fredcox)
2. [Carlos Fagiani Junior](https://github.com/fagianijunior)
3. Geraldo S. Simião Kutz
4. [Mark Wagie](https://github.com/yochananmarqos)

### About Mark Wagie

**Mark Wagie** is Maintainer of the [gonha](https://aur.archlinux.org/packages/gonha) and 
[gonha-git](https://aur.archlinux.org/packages/gonha-git) (AUR) packages for [Arch Linux](https://www.archlinux.org/) 
based distributions and has helped a lot with tips and suggestions for the development 
of this application.

## License 

This project use [MIT License](https://github.com/fredcox/gonha/blob/master/LICENSE)

## Buy me a Coffee

<a href="https://www.buymeacoffee.com/fredcox" target="_blank">
        <img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174">
</a>