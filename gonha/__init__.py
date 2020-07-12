import os
from PyQt5 import QtWidgets, uic, QtCore

resource_path = os.path.join(os.path.split(__file__)[0], './')


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi(f'{resource_path}./mainwindow.ui', self)
        flags = QtCore.Qt.FramelessWindowHint
        flags |= QtCore.Qt.WindowStaysOnBottomHint
        flags |= QtCore.Qt.Tool
        self.hourLabel = self.findChild(QtWidgets.QLabel, 'hourLabel')
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.show()

