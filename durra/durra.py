"""



original src: https://kritascripting.wordpress.com/2018/03/22/bbds-krita-script-starter/
thx brendanscott
"""

import os
import sys
import io

import shutil

from PyQt5 import QtGui
from PyQt5.QtCore import QStandardPaths, QSettings
from PyQt5.QtWidgets import QApplication,  QWidget,  QMessageBox, QFileDialog
from PyQt5.QtXml import QDomDocument, QDomNode
import PyQt5.uic as uic


try:
    from krita import *
    CONTEXT_KRITA = True
    Krita = Krita  # to stop Eric ide complaining about unknown Krita
    EXTENSION = krita.Extension

except ImportError:  # script being run in testing environment without Krita
    CONTEXT_KRITA = False
    EXTENSION = QWidget

TESTING = True
#TESTING = False

from .libdurra.durrabackendext import DURRABackendExt
from .ui_main import Ui_durraDialog


MAIN_KRITA_ID = "durra"
MAIN_KRITA_MENU_ENTRY = "Developer Uses Revision contRoll for Art(-Projects)"


# from LIBRARY_NAME get:
# the name of the directory
# the name of the main python file
# the name of the class

SCRIPT_EXTENSION = "Extension"
SCRIPT_DOCKER = "Docker"

class DURRAExt(EXTENSION, Ui_durraDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.backend = DURRABackendExt(self)

    def setup(self):
        self.backend.setup()
        self.setupUi(self)

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

    def createActions(self, window):
        if CONTEXT_KRITA:
            action = window.createAction(MAIN_KRITA_ID, MAIN_KRITA_MENU_ENTRY)
            # parameter 1 =  the name that Krita uses to identify the action
            # parameter 2 = the text to be added to the menu entry for this script
            action.triggered.connect(self.action_triggered)

    def action_triggered(self):
        self.initDocument()
        self.show()
        self.activateWindow()


    def initDocument(self):
        self.backend.load()

        if self.backend.durradocument.getKritaDocument():
            self.initUIDocumentInfo()
            self.enableButtons()
            self.txtLog.clear()

            if TESTING:
                docInfo = self.backend.durradocument.getDocumentInfo()
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
        if self.backend.durradocument:
            self.txtTitle.setText(self.backend.durradocument.title)
            self.lblEditingTime.setText(self.backend.getDurationText())
            self.txtAuthorFullname.setText(self.backend.durradocument.authorname)
            self.txtAuthorEmail.setText(self.backend.durradocument.authoremail)
            self.txtLicense.setText(self.backend.durradocument.license)
            self.txtRevision.setText(self.backend.durradocument.revisionstr)
            self.txtKeyword.setText(self.backend.durradocument.getKeywordsStr())
            self.lblVersion.setText(self.backend.durradocument.versionstr)
            self.txtDescription.setText(self.backend.durradocument.description)

    def onBtnCancel(self):
        self.close()

    def onBtnSave(self):
        self.txtLog.clear()
        if self.document is not None:
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
        if self.document is not None:
            self.disableButtons()

            output = self.backend.generateDocumentCurrentVersion()

            self.initDocument()
            self.updateVersionArr()
            
            self.txtLog.setPlainText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()

    def onBtnCommitMetaFiles(self):
        self.txtLog.clear()
        if self.document is not None:
            self.disableButtons()

            extramsg = self.txtMessage.toPlainText()
            output = self.backend.commitDocumentMetafilesCurrentVersion(self.document, extramsg)

            self.initDocument(self.document)
            self.updateVersionArr()
            
            self.txtLog.setPlainText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()


    def btnCommitFiles(self):
        self.txtLog.clear()
        if self.document is not None:
            self.disableButtons()

            extramsg = self.txtMessage.toPlainText()
            self.document.save()
            output = self.backend.commitDocumentCurrentVersion(self.document, extramsg)

            self.initDocument(self.document)
            self.updateVersionArr()
            
            self.txtLog.setPlainText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()
            

    def btnNewMajorVersion(self):
        self.txtLog.clear()
        if self.document is not None:
            self.disableButtons()

            extramsg = self.txtMessage.toPlainText()
            self.document.save()
            output = self.backend.commitDocumentNewMajorVersion(self.document, extramsg)

            self.initDocument(self.document)
            self.updateVersionArr()
            
            self.txtLog.setPlainText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()

    def btnNewMinjorVersion(self):
        self.txtLog.clear()
        if self.document is not None:
            self.disableButtons()

            extramsg = self.txtMessage.toPlainText()
            self.document.save()
            output = self.backend.commitDocumentNewMinjorVersion(self.document, extramsg)

            self.initDocument(self.document)
            self.updateVersionArr()
            
            self.txtLog.setPlainText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()

    def btnNewPatchedVersion(self):
        self.txtLog.clear()
        if self.document is not None:
            self.disableButtons()

            extramsg = self.txtMessage.toPlainText()
            self.document.save()
            output = self.backend.commitDocumentNewPatchedVersion(self.document, extramsg)

            self.initDocument(self.document)
            self.updateVersionArr()
            
            self.txtLog.setPlainText(output)
            self.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()


    def btnInitGit(self):
        if self.document is not None:
            self.disableButtons()

            workdir = self.backend.getWorkdir(self.document)
            
            initgit_dir = QFileDialog.getExistingDirectory(
                self.ui,
                "Select a Directory to init git...",
                workdir,
                QFileDialog.ShowDirsOnly
            )

            if initgit_dir is not None and initgit_dir != "":
                
                cmds = [
                    'git init ' + "'" + initgit_dir.replace("'", "'\\''") + "'",
                    'git lfs install',
                    'git lfs track "*.kra"',
                    'git lfs track "_preview.png"'
                ]

                buttonReply = QMessageBox.question(self.ui, 
                                        'Select a Directory to init git...', 
                                        "Are you sure you want to `init git` in " + initgit_dir + "\n\n" +
                                        "Commands to run:\n" + 
                                        "\n".join(cmds)
                                        , 
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if buttonReply == QMessageBox.Yes:
                    self.txtLog.clear()

                    output = ''

                    for cmd in cmds:
                        output = output + '$ ' + cmd + "\n"
                        (out, err) = subprocess.Popen(cmd, cwd=initgit_dir,
                                                      stdout=subprocess.PIPE, shell=True).communicate()
                        
                        output = output + out.decode('UTF-8')
                        self.backend.println(err)


                    src_gitignore_file = os.path.join(self.script_abs_path, ".gitignore")
                    dest_gitignore_file = os.path.join(initgit_dir, ".gitignore")
                    try:
                        if not os.path.exists(dest_gitignore_file):
                            shutil.copyfile(src_gitignore_file, dest_gitignore_file)
                    except IOError as e:
                        output = output + "Unable to copy file: {} {}".format(dest_gitignore_file, e)

                    gitattributes_file = os.path.join(initgit_dir, ".gitattributes")

                    cmds = [
                        'git add ' + dest_gitignore_file,
                        'git add ' + gitattributes_file,
                        'git commit -m "update gitignore and gitattributes"'
                    ]

                    for cmd in cmds:
                        output = output + '$ ' + cmd + "\n"
                        (out, err) = subprocess.Popen(cmd, cwd=initgit_dir,
                                                      stdout=subprocess.PIPE, shell=True).communicate()
                        
                        output = output + out.decode('UTF-8')
                        self.backend.println(err)
                    
                    self.txtLog.setPlainText(output)
                    self.txtLog.moveCursor(QtGui.QTextCursor.End)
                else:
                    pass

            if TESTING:
                docInfo = self.document.documentInfo()
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

        if self.document is not None:
            self.updateVersionArr()
            if self.versionarr is not None:
                if self.versionarr[0] >= 1:
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
            filename = self.document.fileName()
            if filename is None or filename == "":
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

    def updateVersionArr(self):
        self.versionarr = None
        filename = self.document.fileName()
        if filename != "":
            self.versionarr = self.backend.getVERSIONArrFromDoc(self.document)


def main():
    # this includes when the script is run from the command line or
    # from the Scripter plugin.
    if CONTEXT_KRITA:
        # scripter plugin
        # give up - has the wrong context to create widgets etc.
        # maybe in the future change this.
        pass
    else:
        app = QApplication([])

        extension = DURRAExt(None)
        extension.setup()
        extension.action_triggered()
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()

elif CONTEXT_KRITA:
    # And add the extension to Krita's list of extensions:
    app = Krita.instance()
    extension = DURRAExt(parent=app)  # instantiate your class
    app.addExtension(extension)
