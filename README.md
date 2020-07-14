# Gonha

![Gonha - Logo](https://raw.githubusercontent.com/fredcox/gonha/master/gonha/images/logo.png)

* [About](#about)
* [Dependencies](#dependencies)
* [Install](#install)
* [Config](#config)
* [Buy me a Coffee](#buy-me-a-coffee)
* [License](#license)

## About

![Gonha - Logo](https://raw.githubusercontent.com/fredcox/gonha/master/gonha/images/shot1.png)

***Gonha*** is a simple light-weight system monitor for Linux

## Dependencies

1. Pyhton 3.8 or later
2. Fira Code Font

### Installing Fira Code Font

```bash
$ wget https://github.com/tonsky/FiraCode/releases/download/5.2/Fira_Code_v5.2.zip
$ unzip Fira_Code_v5.2.zip -d Fira_Code
$ cd Fira_Code/
$ cp ttf/* ~/.local/share/fonts/
$ fc-cache -v
```

## Install

Remember, ***$HOME/.local/bin*** must be in included in your PATH variable!

```bash
$ pip3 install gonha
$ gonha
```

## Config

After execute gonha for first time the ***$HOME/.config/gonha/config.ini*** is created and
 you need edit to match with network interface in your system. eg

```bash
...
iface = enp5s0
```
By the way, if you want gonha display in ***top left*** section in your screen, please 
***right click*** and switch the position.

In your window manager (Kde, Cinammon, Gnome, Mate, Xfce) settings for startup application specify delay minimun
of ***5 seconds***, this is necessary for ***gonha*** become visible in all workspaces.

See the example above in Cinammon Startup Applications Settings

![Gonha - Startup Applications](https://raw.githubusercontent.com/fredcox/gonha/master/gonha/images/startupdelay.png)

## Screenshot

This is my desktop with Linux Mint 20 and Gonha is top right on the screen.

![Gonha - Screenshot](https://raw.githubusercontent.com/fredcox/gonha/master/gonha/images/gonhascreenshot.png)

## Buy me a Coffee

<a href="https://www.buymeacoffee.com/fredcox" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>


## License 

This project use MIT License