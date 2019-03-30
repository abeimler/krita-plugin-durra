
import os
import sys
import io
import re
import subprocess
from shlex import quote

import shutil

from PyQt5 import QtGui
from PyQt5.QtCore import QStandardPaths, QSettings
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QFileDialog
from PyQt5.QtXml import QDomDocument, QDomNode
import PyQt5.uic as uic


try:
    from krita import *
    CONTEXT_KRITA = True
    Krita = Krita  # to stop Eric ide complaining about unknown Krita
    EXTENSION = krita.Extension
    WIDGET = krita.DockWidget

except ImportError:  # script being run in testing environment without Krita
    CONTEXT_KRITA = False
    EXTENSION = QWidget
    WIDGET = QWidget

TESTING=False

from .libdurra.durrabackendext import DURRABackendExt
from .ui_main import Ui_durraDialog

from .durraext import DURRAExtBase, DURRAExt

MAIN_KRITA_ID = "durra"

class DURRADocker(WIDGET, DURRAExtBase):

    def __init__(self):
        super(DURRADocker, self).__init__()
        self.setWindowTitle("DURRA")

        self.backend = DURRABackendExt()

        self.setup()

    def setup(self):
        self.backend.setup()

        mainWidget = QWidget(self)
        self.setupUi(mainWidget)
        self.setWidget(mainWidget)

        # connect signals
        self.setupConnectionButtons()

        self.disableButtons()
        self.reload()

    def updateLog(self):
        self.txtLog.setPlainText(self.lastlog)

    def canvasChanged(self, canvas):
        self.reload()
        self.txtLog.setPlainText(self.lastlog)

    def createActions(self, window):
        action = window.createAction(MAIN_KRITA_ID, "Generate Meta-Files")
        action.triggered.connect(self.onBtnGenFiles)

        action = window.createAction(MAIN_KRITA_ID, "Commit WIP")
        action.triggered.connect(self.onBtnCommitFiles)

        action = window.createAction(MAIN_KRITA_ID, "Commit gen. Meta-Files")
        action.triggered.connect(self.onBtnCommitMetaFiles)

        action = window.createAction(MAIN_KRITA_ID, "New Major Version")
        action.triggered.connect(self.onBtnNewMajorVersion)

        action = window.createAction(MAIN_KRITA_ID, "New Minjor Version")
        action.triggered.connect(self.onBtnNewMinjorVersion)

        action = window.createAction(MAIN_KRITA_ID, "New Patched Version")
        action.triggered.connect(self.onBtnNewPatchedVersion)
    

    def setupUi(self, mainWidget):
        self.txtMessage = QtWidgets.QTextEdit(mainWidget)
        self.txtMessage.setObjectName("txtMessage")

        self.txtLog = QtWidgets.QTextEdit(mainWidget)
        self.txtLog.setReadOnly(True)
        self.txtLog.setObjectName("txtLog")

        self.btnGenFiles = QtWidgets.QPushButton(mainWidget)
        self.btnGenFiles.setObjectName("btnGenFiles")

        self.btnCommitMetaFiles = QtWidgets.QPushButton(mainWidget)
        self.btnCommitMetaFiles.setObjectName("btnCommitMetaFiles")

        self.btnCommit = QtWidgets.QPushButton(mainWidget)
        self.btnCommit.setMouseTracking(True)
        self.btnCommit.setDefault(True)
        self.btnCommit.setObjectName("btnCommit")
        
        self.btnNewMajorVersion = QtWidgets.QPushButton(mainWidget)
        self.btnNewMajorVersion.setMouseTracking(True)
        self.btnNewMajorVersion.setObjectName("btnNewMajorVersion")

        self.btnNewMinjorVersion = QtWidgets.QPushButton(mainWidget)
        self.btnNewMinjorVersion.setMouseTracking(True)
        self.btnNewMinjorVersion.setObjectName("btnNewMinjorVersion")

        self.btnNewPatchedVersion = QtWidgets.QPushButton(mainWidget)
        self.btnNewPatchedVersion.setMouseTracking(True)
        self.btnNewPatchedVersion.setObjectName("btnNewPatchedVersion")

        self.retranslateUi(mainWidget)
        
        mainWidget.setLayout(QVBoxLayout())
        mainWidget.layout().addWidget(self.txtMessage)
        mainWidget.layout().addWidget(self.txtLog)
        mainWidget.layout().addWidget(self.btnGenFiles)
        mainWidget.layout().addWidget(self.btnCommitMetaFiles)
        mainWidget.layout().addWidget(self.btnCommit)
        mainWidget.layout().addWidget(self.btnNewMajorVersion)
        mainWidget.layout().addWidget(self.btnNewMinjorVersion)
        mainWidget.layout().addWidget(self.btnNewPatchedVersion)
        

    def retranslateUi(self, mainWidget):
        _translate = QtCore.QCoreApplication.translate
        mainWidget.setWindowTitle(_translate("durraDialog", "DURRA"))
        self.txtMessage.setPlaceholderText(_translate("durraDialog", "Commit Message"))
        self.txtLog.setToolTip(_translate("durraDialog", "Log"))
        self.txtLog.setPlaceholderText(_translate("durraDialog", "Log/Output"))
        self.btnGenFiles.setToolTip(_translate("durraDialog", "<html><head/><body><p>generate only Meta-Files: TITLE, DESCRIPTION, KEYWORD, README.md, LICENSE and VERSION</p></body></html>"))
        self.btnGenFiles.setText(_translate("durraDialog", "&Generate Meta-Files"))
        self.btnCommitMetaFiles.setToolTip(_translate("durraDialog", "<html><head/><body><p>generate only Meta-Files: TITLE, DESCRIPTION, KEYWORD, README.md, LICENSE and VERSION</p><p>and make a commit</p><p>(use this if you just want to commit the Meta-Files, not Images)</p><p><br/></p></body></html>"))
        self.btnCommitMetaFiles.setText(_translate("durraDialog", "Commit gen. Meta-&Files"))
        self.btnCommit.setToolTip(_translate("durraDialog", "<html><head/><body><p>save Document</p><p>generate Meta-Files: TITLE, DESCRIPTION, KEYWORD, README.md, LICENSE and VERSION and Images</p><p>make a git commit</p><p>(use this if your Document is still in WIP; if you have already &gt;=1.x.x version use the &quot;New ... Version&quot;-Buttons)</p><p><br/></p></body></html>"))
        self.btnCommit.setText(_translate("durraDialog", "Commit &WIP"))
        self.btnNewMajorVersion.setToolTip(_translate("durraDialog", "<html><head/><body><p>save Document, generate Meta-Files, update Major Version and make a git commit</p><p>(update Major Version if you already finished your Document and totally change stuff; New Version)</p></body></html>"))
        self.btnNewMajorVersion.setText(_translate("durraDialog", "New &Major Version"))
        self.btnNewMinjorVersion.setToolTip(_translate("durraDialog", "<html><head/><body><p>save Document, generate Meta-Files, update Minjor Version and make a git commit</p><p>(update Minjor Version if you already finished your Document and need to add/remove stuff)</p></body></html>"))
        self.btnNewMinjorVersion.setText(_translate("durraDialog", "&New Minjor Version"))
        self.btnNewPatchedVersion.setToolTip(_translate("durraDialog", "<html><head/><body><p>save Document, generate Meta-Files, update Patch/Revision Version and make a git commit</p><p>(update Revision Version if you already finished your Document and fixed just little stuff; nothing new added)</p></body></html>"))
        self.btnNewPatchedVersion.setText(_translate("durraDialog", "New &Patched Version"))


