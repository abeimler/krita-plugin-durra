"""



original src: https://kritascripting.wordpress.com/2018/03/22/bbds-krita-script-starter/
thx brendanscott
"""

import os
import sys

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

#TESTING = True
TESTING = False

from .durrabackendext import *


MAIN_KRITA_ID = "durra"
MAIN_KRITA_MENU_ENTRY = "Developer Uses Revision contRoll for Art(-Projects)"


# from LIBRARY_NAME get:
# the name of the directory
# the name of the main python file
# the name of the class

SCRIPT_EXTENSION = "Extension"
SCRIPT_DOCKER = "Docker`"

UI_FILE = "main.ui"


def load_ui(ui_file):
    """ if this script has been distributed with a ui file in the same directory,
    then find that directory (since it will likely be different from krita's current
    working directory) and use that to load the ui file

    return the loaded ui
    """
    abs_path = os.path.dirname(os.path.realpath(__file__))
    ui_file = os.path.join(abs_path, UI_FILE)
    return uic.loadUi(ui_file)


class DURRAExt(EXTENSION):

    def __init__(self, parent):
        super().__init__(parent)
        self.backend = DURRABackendExt(self)

    def setup(self):
        self.backend.setup()

        self.script_abs_path = os.path.dirname(os.path.realpath(__file__))
        self.ui_file = os.path.join(self.script_abs_path,  UI_FILE)
        self.ui = load_ui(self.ui_file)

        # connect signals
        # self.ui.e_name_of_script.textChanged.connect(self.name_change)
        self.ui.buttonBox.rejected.connect(self.cancel)
        self.ui.btnSave.clicked.connect(self.save)
        self.ui.btnGenFiles.clicked.connect(self.genFiles)
        self.ui.btnCommit.clicked.connect(self.commitFiles)
        self.ui.btnCommitMetaFiles.clicked.connect(self.commitMetaFiles)
        self.ui.btnNewMajorVersion.clicked.connect(self.btnNewMajorVersion)
        self.ui.btnNewMinjorVersion.clicked.connect(self.btnNewMinjorVersion)
        self.ui.btnNewPatchedVersion.clicked.connect(self.btnNewPatchedVersion)
        self.ui.btnInitGit.clicked.connect(self.btnInitGit)

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
        self.ui.show()
        self.ui.activateWindow()

    def cancel(self):
        self.ui.close()

    def initDocument(self, doc=None):
        self.document = doc
        self.versionarr = [0, 0, 0]
        if CONTEXT_KRITA and self.document is None:
            self.document = Krita.instance().activeDocument()

        if self.document is not None:
            filename = self.document.fileName()
            info = self.backend.getDocumentInfo(self.document)
            if filename != "":
                self.versionarr = self.backend.getVERSIONArrFromDoc(
                    self.document)
            self.initUIDocumentInfo(filename, info, self.versionarr)
            self.enableButtons()
            self.ui.txtLog.clear()
        else:
            self.ui.lblFilename.setText('document not open')
            self.ui.txtTitle.clear()
            self.ui.lblEditingTime.clear()
            self.ui.txtAuthorFullname.clear()
            self.ui.txtAuthorEmail.clear()
            self.ui.txtLicense.clear()
            self.ui.txtRevision.clear()
            self.ui.txtKeyword.clear()
            self.ui.lblVersion.clear()
            self.ui.txtDescription.clear()
            self.ui.txtLog.clear()
            self.disableButtons()

    def initUIDocumentInfo(self, filename, info, versionarr):
        self.ui.lblFilename.setText(filename)
        if info:
            self.ui.txtTitle.setText(info['title'])
            self.ui.lblEditingTime.setText(
                self.backend.getDurationText(info['editingtimestr']))
            self.ui.txtAuthorFullname.setText(info['authorname'])
            self.ui.txtAuthorEmail.setText(info['authoremail'])
            self.ui.txtLicense.setText(info['license'])
            self.ui.txtRevision.setText(info['revisionstr'])
            self.ui.txtKeyword.setText(info['keyword'])
            self.ui.lblVersion.setText(self.backend.ver_str(versionarr))
            self.ui.txtDescription.setText(info['description'])

    def save(self):
        self.ui.txtLog.clear()
        if self.document is not None:
            self.disableButtons()
            succ = self.document.save()
            self.initDocument(self.document)
            self.updateVersionArr()

            output = ""
            if succ:
                output = "Document saved"
            else:
                output = "Can't save Document"

            self.ui.txtLog.setText(output)
            self.ui.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()

    def genFiles(self):
        self.ui.txtLog.clear()
        if self.document is not None:
            self.disableButtons()
            # TODO refactoring the "... True, False, True) -"Params" into a Propertie-Object or something
            output = self.backend.commitDocument(
                self.document, None, False, False, True)
            self.initDocument(self.document)
            self.updateVersionArr()

            self.ui.txtLog.setText(output)
            self.ui.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()

    def commitMetaFiles(self):
        self.ui.txtLog.clear()
        if self.document is not None:
            self.disableButtons()
            output = self.backend.commitDocument(
                self.document, None, True, False, True)
            self.initDocument(self.document)
            self.updateVersionArr()

            self.ui.txtLog.setText(output)
            self.ui.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()

    def commitFiles(self):
        self.ui.txtLog.clear()
        if self.document is not None:
            self.disableButtons()
            self.document.save()
            output = self.backend.commitDocumentCurrentVersion(self.document)
            self.initDocument(self.document)
            self.updateVersionArr()

            self.ui.txtLog.setText(output)
            self.ui.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()

    def btnNewMajorVersion(self):
        self.ui.txtLog.clear()
        if self.document is not None:
            self.disableButtons()
            self.document.save()
            output = self.backend.commitDocumentNewMajorVersion(self.document)
            self.initDocument(self.document)
            self.updateVersionArr()

            self.ui.txtLog.setText(output)
            self.ui.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()

    def btnNewMinjorVersion(self):
        self.ui.txtLog.clear()
        if self.document is not None:
            self.disableButtons()
            self.document.save()
            output = self.backend.commitDocumentNewMinjorVersion(self.document)
            self.initDocument(self.document)
            self.updateVersionArr()

            self.ui.txtLog.setText(output)
            self.ui.txtLog.moveCursor(QtGui.QTextCursor.End)
            self.enableButtons()

    def btnNewPatchedVersion(self):
        self.ui.txtLog.clear()
        if self.document is not None:
            self.disableButtons()
            self.document.save()
            output = self.backend.commitDocumentNewPatchedVersion(
                self.document)
            self.initDocument(self.document)
            self.updateVersionArr()

            self.ui.txtLog.setText(output)
            self.ui.txtLog.moveCursor(QtGui.QTextCursor.End)
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

                info = self.backend.getDocumentInfo(self.document)
                authorname = info['authorname']
                authoremail = info['authoremail']
                
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
                    self.ui.txtLog.clear()

                    output = ''

                    for cmd in cmds:
                        output = output + '$ ' + cmd + "\n"
                        (out, err) = subprocess.Popen(cmd, cwd=initgit_dir,
                                                      stdout=subprocess.PIPE, shell=True).communicate()
                        
                        output = output + out.decode('UTF-8')
                        #print(err)


                    src_gitignore_file = os.path.join(self.script_abs_path, ".gitignore")
                    dest_gitignore_file = os.path.join(initgit_dir, ".gitignore")
                    try:
                        if not os.path.exists(dest_gitignore_file):
                            shutil.copyfile(src_gitignore_file, dest_gitignore_file)
                    except IOError as e:
                        output = output + "Unable to copy file: {} {}".format(dest_gitignore_file, e)


                    self.ui.txtLog.setText(output)
                    self.ui.txtLog.moveCursor(QtGui.QTextCursor.End)
                else:
                    pass

            self.enableButtons()

    def disableButtons(self):
        self.ui.btnSave.setEnabled(False)
        self.ui.btnGenFiles.setEnabled(False)
        self.ui.btnCommit.setEnabled(False)
        self.ui.btnCommitMetaFiles.setEnabled(False)
        self.ui.btnNewMajorVersion.setEnabled(False)
        self.ui.btnNewMinjorVersion.setEnabled(False)
        self.ui.btnNewPatchedVersion.setEnabled(False)
        self.ui.btnInitGit.setEnabled(False)

    def enableButtons(self):
        self.ui.btnSave.setEnabled(True)
        self.ui.btnGenFiles.setEnabled(True)
        self.ui.btnCommit.setEnabled(True)
        self.ui.btnCommitMetaFiles.setEnabled(True)
        self.ui.btnNewMajorVersion.setEnabled(True)
        self.ui.btnNewMinjorVersion.setEnabled(True)
        self.ui.btnNewPatchedVersion.setEnabled(True)
        self.ui.btnInitGit.setEnabled(True)

        if self.document is not None:
            self.updateVersionArr()
            if self.versionarr is not None:
                if self.versionarr[0] >= 1:
                    self.ui.btnCommit.setEnabled(False)
                    self.ui.btnCommitMetaFiles.setEnabled(True)
                    self.ui.btnNewMajorVersion.setEnabled(True)
                    self.ui.btnNewMinjorVersion.setEnabled(True)
                    self.ui.btnNewPatchedVersion.setEnabled(True)
                else:
                    self.ui.btnCommit.setEnabled(True)
                    self.ui.btnCommitMetaFiles.setEnabled(True)
                    self.ui.btnNewMajorVersion.setEnabled(True)
                    self.ui.btnNewMinjorVersion.setEnabled(False)
                    self.ui.btnNewPatchedVersion.setEnabled(False)
            filename = self.document.fileName()
            if filename is None or filename == "":
                self.ui.btnGenFiles.setEnabled(False)
                self.ui.btnCommit.setEnabled(False)
                self.ui.btnCommitMetaFiles.setEnabled(False)
                self.ui.btnNewMajorVersion.setEnabled(False)
                self.ui.btnNewMinjorVersion.setEnabled(False)
                self.ui.btnNewPatchedVersion.setEnabled(False)
        else:
            self.ui.btnSave.setEnabled(False)
            self.ui.btnGenFiles.setEnabled(False)
            self.ui.btnCommitMetaFiles.setEnabled(False)
            self.ui.btnCommit.setEnabled(False)
            self.ui.btnNewMajorVersion.setEnabled(False)
            self.ui.btnNewMinjorVersion.setEnabled(False)
            self.ui.btnNewPatchedVersion.setEnabled(False)

    def updateVersionArr(self):
        self.versionarr = None
        filename = self.document.fileName()
        if filename != "":
            self.versionarr = self.backend.getVERSIONArrFromDoc(self.document)



if __name__ == "__main__":
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

elif CONTEXT_KRITA:
    # And add the extension to Krita's list of extensions:
    app = Krita.instance()
    extension = DURRAExt(parent=app)  # instantiate your class
    if not TESTING:
        app.addExtension(extension)
