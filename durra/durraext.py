"""

original src: https://kritascripting.wordpress.com/2018/03/22/bbds-krita-script-starter/
thx brendanscott
"""

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


MAIN_KRITA_ID = "durra"
MAIN_KRITA_MENU_ENTRY = "Developer Uses Revision contRoll for Art(-Projects)"


class DURRAExtBase(object):

    def __init__(self):
        self.backend = DURRABackendExt()

        self.lastlog = ""

        # add more dirs and stuff, setup, ...
        app_data_location = QStandardPaths.AppDataLocation
        pykrita_directory = QStandardPaths.writableLocation(app_data_location)
        if not CONTEXT_KRITA:
            pykrita_directory = os.path.join(pykrita_directory, "krita")
        pykrita_directory = os.path.join(pykrita_directory, "pykrita")
        self.pykrita_directory = pykrita_directory

        self.script_abs_path = os.path.dirname(os.path.realpath(__file__))

    def setupConnectionButtons(self):
        self.btnGenFiles.clicked.connect(self.onBtnGenFiles)
        self.btnCommit.clicked.connect(self.onBtnCommitFiles)
        self.btnCommitMetaFiles.clicked.connect(self.onBtnCommitMetaFiles)
        self.btnNewMajorVersion.clicked.connect(self.onBtnNewMajorVersion)
        self.btnNewMinjorVersion.clicked.connect(self.onBtnNewMinjorVersion)
        self.btnNewPatchedVersion.clicked.connect(self.onBtnNewPatchedVersion)

    def initDocument(self):
        self.backend.load()

        if self.backend.durradocument.hasKritaDocument():
            self.enableButtons()
        else:
            self.disableButtons()
    
    def reload(self):
        self.initDocument()
        if not self.hasKritaDocument():
            self.lastlog = "document is not set"
        
    def updateLog(self):
        pass

    def onBtnSave(self):
        self.lastlog = ""
        if self.hasKritaDocument():
            self.disableButtons()
            succ = self.backend.save()

            if succ:
                self.lastlog = "Document saved"
            else:
                self.lastlog = "Can't save Document"

            self.enableButtons()
        return self.lastlog

    def onBtnGenFiles(self):
        self.lastlog = ""
        if self.hasKritaDocument():
            self.disableButtons()

            self.lastlog = self.backend.generateDocumentCurrentVersion()
            self.reload()
            
            self.enableButtons()
            self.updateLog()
        return self.lastlog
    
    def onBtnCommitMetaFiles(self, extramsg):
        if not self.isGitRepo():
            self.lastlog = "not a git repository (or any of the parent directories)"
            return self.lastlog
        
        self.lastlog = ""
        if self.hasKritaDocument() and self.isGitRepo():
            self.disableButtons()

            self.backend.save()

            self.lastlog = self.backend.commitDocumentMetafilesCurrentVersion(extramsg)
            self.reload()
            
            self.enableButtons()
            self.updateLog()
        return self.lastlog


    def onBtnCommitFiles(self, extramsg):
        if not self.isGitRepo():
            self.lastlog = "not a git repository (or any of the parent directories)"
            self.updateLog()
            return self.lastlog
        
        if self.isReleasedVersion():
            self.lastlog = "it's released already (version >= 1.0.0)"
            self.updateLog()
            return self.lastlog
        
        self.lastlog = ""
        if self.hasKritaDocument() and self.isGitRepo() and not self.isReleasedVersion():
            self.disableButtons()

            self.backend.save()

            self.lastlog = self.backend.commitDocumentCurrentVersion(extramsg)
            self.reload()
            
            self.enableButtons()
            self.updateLog()
        return self.lastlog
            

    def onBtnNewMajorVersion(self, extramsg):
        if not self.isGitRepo():
            self.lastlog = "not a git repository (or any of the parent directories)"
            self.updateLog()
            return self.lastlog
        
        self.lastlog = ""
        if self.hasKritaDocument() and self.isGitRepo():
            self.disableButtons()

            self.backend.save()

            self.lastlog = self.backend.commitDocumentNewMajorVersion(extramsg)
            self.reload()
            
            self.enableButtons()
            self.updateLog()
        return self.lastlog

    def onBtnNewMinjorVersion(self, extramsg):
        if not self.isGitRepo():
            self.lastlog = "not a git repository (or any of the parent directories)"
            self.updateLog()
            return self.lastlog
        
        if not self.isReleasedVersion():
            self.lastlog = "not a released version (version < 1.0.0)"
            self.updateLog()
            return self.lastlog
        
        self.lastlog = ""
        if self.hasKritaDocument() and self.isGitRepo() and self.isReleasedVersion():
            self.disableButtons()

            self.backend.save()

            self.lastlog = self.backend.commitDocumentNewMinjorVersion(extramsg)
            self.reload()
            
            self.enableButtons()
            self.updateLog()
        return self.lastlog

    def onBtnNewPatchedVersion(self, extramsg):
        if not self.isGitRepo():
            self.lastlog = "not a git repository (or any of the parent directories)"
            self.updateLog()
            return self.lastlog
        
        if not self.isReleasedVersion():
            self.lastlog = "not a released version (version < 1.0.0)"
            self.updateLog()
            return self.lastlog
        
        self.lastlog = ""
        if self.hasKritaDocument() and self.isGitRepo() and self.isReleasedVersion():
            self.disableButtons()

            self.backend.save()

            self.lastlog = self.backend.commitDocumentNewPatchedVersion(extramsg)
            self.reload()
            
            self.enableButtons()
            self.updateLog()
        return self.lastlog



    def disableButtons(self):
        self.btnGenFiles.setEnabled(False)
        self.btnCommit.setEnabled(False)
        self.btnCommitMetaFiles.setEnabled(False)
        self.btnNewMajorVersion.setEnabled(False)
        self.btnNewMinjorVersion.setEnabled(False)
        self.btnNewPatchedVersion.setEnabled(False)

    def isReleasedVersion(self):
        if self.backend.durradocument.hasKritaDocument():
            if self.backend.durradocument.getVERSIONArr():
                return self.backend.durradocument.getVERSIONArr()[0] >= 1
        return False

    def isSavedFile(self):
        if self.backend.durradocument.hasKritaDocument():
            return self.backend.durradocument.getFilenameKra()
        return False

    def isGitRepo(self):
        return self.backend.gitIsRepo(self.backend.workdir)

    def hasKritaDocument(self):
        return self.backend.durradocument.hasKritaDocument()

    def enableButtons(self):
        self.btnGenFiles.setEnabled(True)
        self.btnCommit.setEnabled(True)
        self.btnCommitMetaFiles.setEnabled(True)
        self.btnNewMajorVersion.setEnabled(True)
        self.btnNewMinjorVersion.setEnabled(True)
        self.btnNewPatchedVersion.setEnabled(True)

        if self.hasKritaDocument():
            if self.isReleasedVersion():
                self.btnCommit.setEnabled(False)
                self.btnCommitMetaFiles.setEnabled(True)
                self.btnNewMajorVersion.setEnabled(True)
                self.btnNewMinjorVersion.setEnabled(True)
                self.btnNewPatchedVersion.setEnabled(True)
            else:
                self.btnCommit.setEnabled(True)
                self.btnCommitMetaFiles.setEnabled(True)
                self.btnNewMajorVersion.setEnabled(True)
                self.btnNewMinjorVersion.setEnabled(False)
                self.btnNewPatchedVersion.setEnabled(False)
            
            if not self.isSavedFile():
                self.btnCommit.setEnabled(False)
                self.btnCommitMetaFiles.setEnabled(False)
                self.btnNewMajorVersion.setEnabled(False)
                self.btnNewMinjorVersion.setEnabled(False)
                self.btnNewPatchedVersion.setEnabled(False)

            if not self.isGitRepo():
                self.btnCommit.setEnabled(False)
                self.btnCommitMetaFiles.setEnabled(False)
                self.btnNewMajorVersion.setEnabled(False)
                self.btnNewMinjorVersion.setEnabled(False)
                self.btnNewPatchedVersion.setEnabled(False)
        else:
            self.btnGenFiles.setEnabled(False)
            self.btnCommitMetaFiles.setEnabled(False)
            self.btnCommit.setEnabled(False)
            self.btnNewMajorVersion.setEnabled(False)
            self.btnNewMinjorVersion.setEnabled(False)
            self.btnNewPatchedVersion.setEnabled(False)



class DURRAExt(EXTENSION, DURRAExtBase, Ui_durraDialog):

    def __init__(self, parent):
        super(DURRAExt, self).__init__(parent)

        self.backend = DURRABackendExt()

    def setup(self):
        self.backend.setup()

        self.ui = QWidget()
        self.setupUi(self.ui)

        # connect signals
        self.setupConnectionButtons()
        self.buttonBox.rejected.connect(self.onBtnCancel)
        self.btnSave.clicked.connect(self.onBtnSave)
        self.btnInitGit.clicked.connect(self.onBtnInitGit)

        self.disableButtons()


    def createActions(self, window):
        if CONTEXT_KRITA:
            action = window.createAction(MAIN_KRITA_ID, MAIN_KRITA_MENU_ENTRY)
            # parameter 1 =  the name that Krita uses to identify the action
            # parameter 2 = the text to be added to the menu entry for this script
            action.triggered.connect(self.action_triggered)

    def action_triggered(self):
        self.backend.output = ""
        self.initDocument()
        self.ui.show()
        self.ui.activateWindow()

    def onBtnCancel(self):
        self.ui.close()


    def initDocument(self):
        self.txtLog.clear()
        super().initDocument()

        if self.backend.durradocument.hasKritaDocument():
            self.initUIDocumentInfo()

            if TESTING:
                docInfo = self.backend.durradocument.getKritaDocumentInfo()
                self.backend.output = self.backend.output + "\n\n" + docInfo
            
            self.txtLog.setPlainText(self.backend.output)
            
        else:
            self.lblFilename.setText('document not open')
            self.txtTitle.clear()
            self.lblEditingTime.clear()
            self.txtAuthorFullname.clear()
            self.txtAuthorEmail.clear()
            self.txtLicense.clear()
            self.txtRevision.clear()
            self.txtKeyword.clear()
            self.lblVersion.clear()
            self.txtDescription.clear()
            self.txtLog.clear()

    def initUIDocumentInfo(self):
        self.lblFilename.setText(self.backend.durradocument.getFilenameKra())
        if self.backend.durradocument.hasKritaDocument():
            self.txtTitle.setText(self.backend.durradocument.title)
            self.lblEditingTime.setText(self.backend.durradocument.getDurationText())
            self.txtAuthorFullname.setText(self.backend.durradocument.authorname)
            self.txtAuthorEmail.setText(self.backend.durradocument.authoremail)
            self.txtLicense.setText(self.backend.durradocument.license)
            self.txtRevision.setText(self.backend.durradocument.revisionstr)
            self.txtKeyword.setText(self.backend.durradocument.getKeywordsStr())
            self.lblVersion.setText(self.backend.durradocument.versionstr)
            self.txtDescription.setText(self.backend.durradocument.description)

    def onBtnSave(self):
        self.txtLog.clear()
        if self.backend.durradocument.hasKritaDocument():
            self.initUIDocumentInfo()
            output = super().onBtnSave()

            self.txtLog.setText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)

    def onBtnGenFiles(self):
        self.txtLog.clear()
        if self.backend.durradocument.hasKritaDocument():
            output = super().onBtnGenFiles()
            
            self.txtLog.setPlainText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)

    def onBtnCommitMetaFiles(self):
        self.txtLog.clear()
        if self.backend.durradocument.hasKritaDocument():
            extramsg = self.txtMessage.toPlainText()

            output = super().onBtnCommitMetaFiles(extramsg)
            
            self.txtLog.setPlainText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)


    def onBtnCommitFiles(self):
        self.txtLog.clear()
        if self.backend.durradocument.hasKritaDocument():
            extramsg = self.txtMessage.toPlainText()

            output = super().onBtnCommitFiles(extramsg)
            
            self.txtLog.setPlainText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)
            

    def onBtnNewMajorVersion(self):
        self.txtLog.clear()
        if self.backend.durradocument.hasKritaDocument():
            extramsg = self.txtMessage.toPlainText()

            output = super().onBtnNewMajorVersion(extramsg)
            
            self.txtLog.setPlainText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)


    def onBtnNewMinjorVersion(self):
        self.txtLog.clear()
        if self.backend.durradocument.hasKritaDocument():
            extramsg = self.txtMessage.toPlainText()

            output = super().onBtnNewMinjorVersion(extramsg)
            
            self.txtLog.setPlainText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)


    def onBtnNewPatchedVersion(self):
        self.txtLog.clear()
        if self.backend.durradocument.hasKritaDocument():
            extramsg = self.txtMessage.toPlainText()

            output = super().onBtnNewPatchedVersion(extramsg)
            
            self.txtLog.setPlainText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)
    

    def onBtnInitGit(self):
        if self.backend.durradocument.hasKritaDocument():
            self.disableButtons()

            workdir = self.backend.workdir
            
            initgit_dir = QFileDialog.getExistingDirectory(
                self.ui,
                "Select a Directory to init git...",
                workdir,
                QFileDialog.ShowDirsOnly
            )

            if initgit_dir:
                cmds = self.backend.getGitInitCmds(initgit_dir)


                btnMsg = "Are you sure you want to `init git` in " + initgit_dir + "\n\n" + "Commands to run:\n"
                for cmd in cmds:
                    btnMsg = btnMsg + '$ ' + ' '.join(cmd) + "\n"
                
                buttonReply = QMessageBox.question(self.ui, 'Select a Directory to init git...', btnMsg, 
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if buttonReply == QMessageBox.Yes:
                    self.txtLog.clear()

                    output = self.backend.runGitInit(initgit_dir)
                    
                    self.txtLog.setPlainText(output)
                    self.txtLog.moveCursor(QtGui.QTextCursor.End)
                else:
                    pass

            if TESTING:
                docInfo = self.backend.durradocument.getKritaDocumentInfo()
                self.backend.output = self.backend.output + "\n\n" + docInfo
                self.txtLog.setToolTip(self.backend.output)

            self.enableButtons()

    def disableButtons(self):
        super().disableButtons()
        self.btnSave.setEnabled(False)
        self.btnInitGit.setEnabled(False)

    def enableButtons(self):
        super().enableButtons()

        self.btnSave.setEnabled(True)
        self.btnInitGit.setEnabled(True)

        if self.backend.durradocument.hasKritaDocument():
            if not self.backend.gitIsRepo(self.backend.workdir):
                self.btnInitGit.setEnabled(True)
            else:
                self.btnInitGit.setEnabled(False)
        else:
            self.btnSave.setEnabled(False)
