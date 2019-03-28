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


# from LIBRARY_NAME get:
# the name of the directory
# the name of the main python file
# the name of the class

class DURRAExt(Ui_durraDialog, EXTENSION):

    def __init__(self, parent):
        super(DURRAExt, self).__init__(parent)
        self.backend = DURRABackendExt(parent)

    def setup(self):
        self.backend.setup()

        self.ui = QWidget()
        self.setupUi(self.ui)

        # connect signals
        # self.e_name_of_script.textChanged.connect(self.name_change)
        self.buttonBox.rejected.connect(self.onBtnCancel)
        self.btnSave.clicked.connect(self.onBtnSave)
        self.btnGenFiles.clicked.connect(self.onBtnGenFiles)
        self.btnCommit.clicked.connect(self.onBtnCommitFiles)
        self.btnCommitMetaFiles.clicked.connect(self.onBtnCommitMetaFiles)
        self.btnNewMajorVersion.clicked.connect(self.onBtnNewMajorVersion)
        self.btnNewMinjorVersion.clicked.connect(self.onBtnNewMinjorVersion)
        self.btnNewPatchedVersion.clicked.connect(self.onBtnNewPatchedVersion)
        self.btnInitGit.clicked.connect(self.onBtnInitGit)

        self.disableButtons()

        # add more dirs and stuff, setup, ...
        app_data_location = QStandardPaths.AppDataLocation
        pykrita_directory = QStandardPaths.writableLocation(app_data_location)
        if not CONTEXT_KRITA:
            pykrita_directory = os.path.join(pykrita_directory, "krita")
        pykrita_directory = os.path.join(pykrita_directory, "pykrita")
        self.pykrita_directory = pykrita_directory

        self.script_abs_path = os.path.dirname(os.path.realpath(__file__))

    def createActions(self, window):
        if CONTEXT_KRITA:
            action = window.createAction(MAIN_KRITA_ID, MAIN_KRITA_MENU_ENTRY)
            # parameter 1 =  the name that Krita uses to identify the action
            # parameter 2 = the text to be added to the menu entry for this script
            action.triggered.connect(self.action_triggered)

    def action_triggered(self):
        self.initDocument()
        self.ui.show()
        self.ui.activateWindow()

    def onBtnCancel(self):
        self.ui.close()

    def reload(self):
        self.initDocument();

    def initDocument(self):
        self.backend.load()

        if self.backend.durradocument.hasKritaDocument():
            self.initUIDocumentInfo()
            self.enableButtons()
            self.txtLog.clear()

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
            self.disableButtons()

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
            self.disableButtons()
            succ = self.backend.save()
            self.initUIDocumentInfo()

            output = ""
            if succ:
                output = "Document saved"
            else:
                output = "Can't save Document"

            self.txtLog.setText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()

    def onBtnGenFiles(self):
        self.txtLog.clear()
        if self.backend.durradocument.hasKritaDocument():
            self.disableButtons()

            output = self.backend.generateDocumentCurrentVersion()

            self.initDocument()
            
            self.txtLog.setPlainText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()

    def onBtnCommitMetaFiles(self):
        self.txtLog.clear()
        if self.backend.durradocument.hasKritaDocument():
            self.disableButtons()

            self.backend.save()

            extramsg = self.txtMessage.toPlainText()
            output = self.backend.commitDocumentMetafilesCurrentVersion(extramsg)

            self.initDocument()
            
            self.txtLog.setPlainText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()


    def onBtnCommitFiles(self):
        self.txtLog.clear()
        if self.backend.durradocument.hasKritaDocument():
            self.disableButtons()

            self.backend.save()

            extramsg = self.txtMessage.toPlainText()
            output = self.backend.commitDocumentCurrentVersion(extramsg)

            self.reload()
            
            self.txtLog.setPlainText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()
            

    def onBtnNewMajorVersion(self):
        self.txtLog.clear()
        if self.backend.durradocument.hasKritaDocument():
            self.disableButtons()

            self.backend.save()

            extramsg = self.txtMessage.toPlainText()
            output = self.backend.commitDocumentNewMajorVersion(extramsg)

            self.reload()
            
            self.txtLog.setPlainText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()

    def onBtnNewMinjorVersion(self):
        self.txtLog.clear()
        if self.backend.durradocument.hasKritaDocument():
            self.disableButtons()

            self.backend.save()

            extramsg = self.txtMessage.toPlainText()
            output = self.backend.commitDocumentNewMinjorVersion(extramsg)

            self.reload()
            
            self.txtLog.setPlainText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()

    def onBtnNewPatchedVersion(self):
        self.txtLog.clear()
        if self.backend.durradocument.hasKritaDocument():
            self.disableButtons()

            self.backend.save()

            extramsg = self.txtMessage.toPlainText()
            output = self.backend.commitDocumentNewPatchedVersion(extramsg)

            self.reload()
            
            self.txtLog.setPlainText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()
    
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
                cmds = [
                    ['git', 'init ', quote(initgit_dir)],
                    ['git', 'lfs', 'install'],
                    ['git', 'lfs', 'track', '"*.kra"'],
                    ['git', 'lfs', 'track', '"*.png"'],
                    ['git', 'lfs', 'track', '"_preview.png"']
                ]


                btnMsg = "Are you sure you want to `init git` in " + initgit_dir + "\n\n" + "Commands to run:\n"
                for cmd in cmds:
                    btnMsg = btnMsg + '$ ' + ' '.join(cmd) + "\n"
                
                buttonReply = QMessageBox.question(self.ui, 'Select a Directory to init git...', btnMsg, 
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if buttonReply == QMessageBox.Yes:
                    self.txtLog.clear()

                    output = ''

                    for cmd in cmds:
                        output = output + self.backend.runCmd(cmd, workdir)


                    src_gitignore_file = os.path.join(self.script_abs_path, ".gitignore")
                    dest_gitignore_file = os.path.join(initgit_dir, ".gitignore")
                    try:
                        if not os.path.exists(dest_gitignore_file):
                            shutil.copyfile(src_gitignore_file, dest_gitignore_file)
                    except IOError as e:
                        output = output + "Unable to copy file: {} {}".format(dest_gitignore_file, e)

                    gitattributes_file = os.path.join(initgit_dir, ".gitattributes")

                    cmds = [
                        ['git', 'add ', quote(dest_gitignore_file)],
                        ['git', 'add ', quote(gitattributes_file)],
                        ['git', 'commit', '-m', '"update gitignore and gitattributes"']
                    ]

                    for cmd in cmds:
                        output = output + self.backend.runCmd(cmd, workdir)
                    
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
        self.btnSave.setEnabled(False)
        self.btnGenFiles.setEnabled(False)
        self.btnCommit.setEnabled(False)
        self.btnCommitMetaFiles.setEnabled(False)
        self.btnNewMajorVersion.setEnabled(False)
        self.btnNewMinjorVersion.setEnabled(False)
        self.btnNewPatchedVersion.setEnabled(False)
        self.btnInitGit.setEnabled(False)

    def enableButtons(self):
        self.btnSave.setEnabled(True)
        self.btnGenFiles.setEnabled(True)
        self.btnCommit.setEnabled(True)
        self.btnCommitMetaFiles.setEnabled(True)
        self.btnNewMajorVersion.setEnabled(True)
        self.btnNewMinjorVersion.setEnabled(True)
        self.btnNewPatchedVersion.setEnabled(True)
        self.btnInitGit.setEnabled(True)

        if self.backend.durradocument.hasKritaDocument():
            if self.backend.durradocument.getVERSIONArr():
                if self.backend.durradocument.getVERSIONArr()[0] >= 1:
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
            
            if not self.backend.durradocument.getFilenameKra():
                self.btnGenFiles.setEnabled(False)
                self.btnCommit.setEnabled(False)
                self.btnCommitMetaFiles.setEnabled(False)
                self.btnNewMajorVersion.setEnabled(False)
                self.btnNewMinjorVersion.setEnabled(False)
                self.btnNewPatchedVersion.setEnabled(False)
        else:
            self.btnSave.setEnabled(False)
            self.btnGenFiles.setEnabled(False)
            self.btnCommitMetaFiles.setEnabled(False)
            self.btnCommit.setEnabled(False)
            self.btnNewMajorVersion.setEnabled(False)
            self.btnNewMinjorVersion.setEnabled(False)
            self.btnNewPatchedVersion.setEnabled(False)
