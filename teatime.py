#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import datetime
import logging
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QObject, pyqtSignal, pyqtSlot

"""
timer application (tea timer) written in pyqt

author: hgue
mail:   web@b2.anyalias.com
date:   25.10.2016
"""

log = logging.getLogger('main')

# list entry name, id,
cookTypes = ( (4, "Black tea",           180),
              (3, "Fruit tea",           480),
              (2, "Pizza",               780),
              (1, "Cake",                1800),
              (0, "Custom",              0)
            )

class CookTimerView(QtGui.QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        teaImage = QtGui.QPixmap("teatime.png")

        # create controls
        self.lblTeaCup = QtGui.QLabel()
        self.lblTeaCup.setPixmap(teaImage)
        self.lblCookTimeInfo = QtGui.QLabel()
        self.btnTimerControl = QtGui.QPushButton("Start Timer")
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setTextVisible(True)
        self.cmbCookType = QtGui.QComboBox()

        # set size policies
        self.cmbCookType.setMinimumSize(QtCore.QSize(200,20))
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.cmbCookType.setSizePolicy(sizePolicy)
        self.btnTimerControl.setSizePolicy(sizePolicy)

        self._initLayout()

        # create presenter
        self._presenter = CookTimerPresenter(self)

        self._initEvents()
        self._initDefaults()

        self.setWindowTitle('Tea Timer')
        self.setWindowIcon(QtGui.QIcon(teaImage))
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.show()

    def _initDefaults(self):
        # select first entry in combobox for cook types
        self._currentIndexChanged(0)

    def _initLayout(self):
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.cmbCookType)
        vbox.addWidget(self.btnTimerControl)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.lblTeaCup)
        hbox.addLayout(vbox)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(hbox)
        layout.addWidget(self.progressBar)
        layout.addWidget(self.lblCookTimeInfo)
        self.setLayout(layout)

    def _initEvents(self):
        self.cmbCookType.currentIndexChanged.connect(self._currentIndexChanged)
        self.btnTimerControl.clicked.connect(self._timerControlEvent)

    def _timerControlEvent(self):
        self._presenter.timerUserControlEvent()

    def _currentIndexChanged(self, index):
        self._curCookTypeName = self.cmbCookType.currentText()
        self._curCookTypeId = self.cmbCookType.itemData(index)
        self._presenter.cookTypeUserControlEvent()
        print("Selected cook type: " + str(self._curCookTypeName) + " - " + str(self._curCookTypeId))

    def askUserForCookTime(self) -> int:
        """
        @return seconds entered by user or None if canceled
        """
        userMinutes, ok = QtGui.QInputDialog.getInt(self, "custom timer", "minutes :", 5, 0, 300, 1)
        if (ok):
            return userMinutes * 60
        else:
            return None

    def getSelectedCookTypeId(self) -> int:
        return int(self._curCookTypeId)

    def updateCookTimeProgressBar(self, secondsTotal: int, secondsElapsed: int):
        self.progressBar.setMaximum(secondsTotal)
        if (secondsElapsed <= secondsTotal and secondsElapsed >= 0):
            self.progressBar.setValue(secondsElapsed)

        self.lblCookTimeInfo.setText(self.secondsFormatTime(secondsElapsed) + " / " + self.secondsFormatTime(secondsTotal))

    def secondsFormatTime(self, seconds: int) -> str:
        return "{}".format(datetime.timedelta(seconds=seconds))

    def timerStoppedEvent(self):
        self.btnTimerControl.setText("Start timer")

    def timerStartEvent(self):
        self.btnTimerControl.setText("Stop timer")

    def showTimerElapsedMessage(self, message: str):
        msgBox = QtGui.QMessageBox()
        msgBox.setIcon(QtGui.QMessageBox.Information)
        msgBox.setText(message)
        msgBox.setWindowTitle("Timer elapsed!")
        font = QtGui.QFont("Arial",12,QtGui.QFont.Bold)
        msgBox.setFont(font)
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, QtCore.Qt.magenta)
        msgBox.setPalette(palette)
        msgBox.exec_()

    def addCookTypeEntry(self, id: int, name: str, cookTimeSeconds: int = 0):
        # if time is not unspecified, display cooking time in combobox
        if (cookTimeSeconds != 0):
            entryName = "{} - {}".format(name, self.secondsFormatTime(cookTimeSeconds))
        else:
            entryName = name
        self.cmbCookType.addItem(entryName, id)

class CookTimerPresenter(QtCore.QObject):

    def __init__(self, cookTimerView: CookTimerView):
        QObject.__init__(self)

        self._view = cookTimerView

        self._startTime = None
        self._stopTime = None
        self._totalTime = None

        self._init()

    def _init(self):
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.timerCountEvent)
        self.loadCookTypes()

    def _getCookTypeNameById(self, id: int) -> str:
        for i in cookTypes:
            if (i[0] == id):
                return i[1]
        raise ValueError("Unknown id: " + str(id))

    def _getCookTypeTimeById(self, id: int) -> int:
        for i in cookTypes:
            if (i[0] == id):
                return i[2]
        raise ValueError("Unknown id: " + str(id))

    def _loadCookTypeFromView(self) -> bool:
        cookTypeId = self._view.getSelectedCookTypeId()

        # user specific time?
        if (cookTypeId == 0):
            userSeconds = self._view.askUserForCookTime()
            if (userSeconds is not None):
                self._curCookTime = userSeconds
                self._curCookName = self._getCookTypeNameById(cookTypeId)
                return True
            else:
                return False
        else:
            self._curCookTime = self._getCookTypeTimeById(cookTypeId)
            self._curCookName = self._getCookTypeNameById(cookTypeId)
            return True

    def timerStart(self):
        if (not self._loadCookTypeFromView()):
            return

        self._totalTime = datetime.timedelta(seconds = self._curCookTime)

        self._startTime = datetime.datetime.now()
        self._stopTime = self._startTime + self._totalTime

        self._timer.start(1000)
        self._view.timerStartEvent()

        minutes = int(float(self._curCookTime)/60)
        print("Timer started: " + self._curCookName + " - " + str(minutes) + " min.")

    def timerStop(self):
        self._view.updateCookTimeProgressBar(self._totalTime.seconds, 0)
        self._view.timerStoppedEvent()
        self._timer.stop()
        print("Timer stopped")

    def cookTypeUserControlEvent(self):
        if (self._timer.isActive()):
            self.timerStop()

    def timerUserControlEvent(self):
        if (not self._timer.isActive()):
            self.timerStart()
        else:
            self.timerStop()

    @QtCore.pyqtSlot()
    def timerCountEvent(self):
        if (self._stopTime is not None):
            timeNow = datetime.datetime.now()
            if (timeNow > self._stopTime):
                print("Timer elapsed!")
                self._view.showTimerElapsedMessage(self._curCookName + " -> Timer elapsed!")
                self.timerStop()
            else:
                secondsElapsed = (timeNow - self._startTime).seconds
                self._view.updateCookTimeProgressBar(self._totalTime.seconds, secondsElapsed)

    def loadCookTypes(self):
        for t in cookTypes:
            self._view.addCookTypeEntry(t[0], t[1], t[2])

def main():
    app = QtGui.QApplication(sys.argv)
    v = CookTimerView()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
