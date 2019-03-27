import os
import sys

import re
import subprocess
from shlex import quote

from PyQt5.QtCore import QStandardPaths, QSettings
from PyQt5.QtWidgets import QApplication,  QWidget,  QMessageBox
import PyQt5.uic as uic
from PyQt5.QtXml import QDomDocument

try:
    import krita
    CONTEXT_KRITA = True
    Krita = Krita  # to stop Eric ide complaining about unknown Krita
    EXTENSION = krita.Extension

except ImportError:  # script being run in testing environment without Krita
    CONTEXT_KRITA = False
    EXTENSION = QWidget

from .durradocumentkrita import DURRADocumentKrita

#TESTING = True
#TESTING = False


class DURRABackendExt(EXTENSION):
    PREVIEW_SCALE = 0.5

    def __init__(self, parent):
        super().__init__(parent)

        self.durradocument = DURRADocumentKrita()
        self.workdir = ""

        self.output = ""

    def setup(self):
        self.output = ""
        self.load()

    def _getWorkdir(self, filename_kra):
        if filename_kra != "":
            filename_path = os.path.dirname(os.path.realpath(filename_kra))
            work_filename_path = os.path.basename(
                os.path.normpath(filename_path))
            workdir = filename_path
            if work_filename_path == "work":
                workdir = os.path.dirname(os.path.realpath(filename_path))
            #workdir_basename = os.path.basename(os.path.normpath(workdir))
            return workdir

        return ""
    
    def load(self):
        if CONTEXT_KRITA:
            document = Krita.instance().activeDocument()
            filename_kra = document.fileName()
            self.workdir = self._getWorkdir(filename_kra)

            self.durradocument.loadVersionFromWorkdir(self.workdir)
            self.durradocument.loadDocument(document)
    
    def save(self):
        if CONTEXT_KRITA:
            if self.durradocument.document:
                succ = self.durradocument.document.save()
                self.durradocument.loadDocument(self.durradocument.document)
                return succ
        return False

    def println(self, str):
        if str is not None:
            self.output = self.output + str + '\n'

    def makeMetaFiles(self):
        if not self.durradocument.filename_name:
            self.println('filename is empty')
            return []

        files = self.durradocument.makeMetaFiles(self.workdir)

        return files
    
    def makeFiles(self):
        if not self.durradocument.filename_name:
            self.println('filename is empty')
            return []

        files = self.durradocument.makeFiles(self.workdir)

        return files

    def runGit(self, workdir, files, msg, description=None, authorname=None, authoremail=None):
        output = ''

        output = output + self._gitAdd(workdir, files)
        output = output + self._gitCommit(workdir, msg, description, authorname, authoremail)

        return output

    def _gitAdd(self, workdir, files):
        output = ''

        for file in files:
            if file:
                cmd = ['git', 'add ', quote(file)]
                (out, err) = subprocess.Popen(cmd, cwd=workdir,
                                              stdout=subprocess.PIPE, shell=True).communicate()

                output = output + '$ ' + cmd + "\n"
                output = output + out.decode('UTF-8')
                self.println(err)
        
        return output

    def _gitCommit(self, workdir, msg, description=None, authorname=None, authoremail=None):
        output = ''

        cmd = ['git', 'commit', '-m',  quote(msg)]
        if description:
            cmd.extend(['-m ', quote(description).replace("\n", "\\n")])
        
        if authorname:
            authorargstr = quote(authorname) 
            if  authoremail:
                authorargstr = quote(authorname + " <" + authoremail + ">")

            authorarg = '--author=' + authorargstr
            cmd.append(authorarg)
        
        (out, err) = subprocess.Popen(cmd, cwd=workdir,
                                      stdout=subprocess.PIPE, shell=True).communicate()

        output = output + '$ ' + cmd + "\n"
        output = output + out.decode('UTF-8')
        
        self.println(err)

        return output

    def generateDocumentMetaFiles(self):
        files = self._generateDocumentFiles(False)
        output = "generate Files: " + "\n - ".join(str(x) for x in files) + "\n\n"
        return output

    def generateDocument(self):
        files = self._generateDocumentFiles(True)
        output = "generate Files: " + "\n - ".join(str(x) for x in files) + "\n\n"
        return output

    def _generateDocumentFiles(self, onlymetafiles=False):
        if self.durradocument.document is not None:
            filename = self.durradocument.filename_kra

            if filename != "":
                files = []
                if onlymetafiles:
                    files = self.makeMetaFiles()
                else:
                    files = self.makeFiles()

                return files
            else:
                self.println('filename is empty')
        else:
            self.println('document is not set')

        return []



    def commitDocumentMetafiles(self, extramsg=None):
        return self._commitDocument(False, extramsg)
    
    def commitDocument(self, extramsg=None):
        return self._commitDocument(True, extramsg)

    def _commitDocument(self, onlymetafiles=False, extramsg=None):
        if self.durradocument.document:
            filename = self.durradocument.filename_kra

            if filename != "":
                files = self._generateDocumentFiles(onlymetafiles)

                name = self.durradocument.document.name()
                workdir_basename = os.path.basename(os.path.normpath(self.workdir))

                outputfiles = "generate Files: " + "\n - ".join(str(x) for x in files) + "\n\n"

                nr = ""
                mnrs = re.search(r"^\s*(\d+)\s+\-\s+.*$", workdir_basename)
                nr = mnrs.group(1) if mnrs is not None else ""
                nrstr = None
                if nr:
                    nrstr = "#{0}".format(int(nr))

                msg = ""

                if self.durradocument.releaseversion and self.durradocument.isnewversion:
                    if self.durradocument.versionstr == "1.0.0":
                        msg = "finished " + name + " v" + self.durradocument.versionstr + " Closes " + nrstr
                    else:
                        msg = "new version of " + name + " v" + self.durradocument.versionstr
                else:
                    msg = "work on "
                    if nrstr is not None:
                        msg = msg + nrstr + " "
                    msg = msg + name

                output = self.runGit(self.workdir, files, msg, extramsg, self.durradocument.authorname, self.durradocument.authoremail)

                return outputfiles + output
            else:
                return 'filename is empty'
        else:
            return 'document is not set'


    def newMajorVersion(self):
        return self.durradocument.newMajorVersion()

    def newMinjorVersion(self):
        return self.durradocument.newMinjorVersion()

    def newPatchVersion(self):
        return self.durradocument.setNewPatchVersion()




    
    def generateDocumentMetafilesCurrentVersion(self):
        if self.durradocument.document is not None:
            return self.generateDocumentMetaFiles()
        else:
            return 'document is not set'
    
    def commitDocumentMetafilesCurrentVersion(self, extramsg=None):
        if self.durradocument.document is not None:
            return self.commitDocumentMetafiles(extramsg)
        else:
            return 'document is not set'

    
    def generateDocumentCurrentVersion(self):
        if self.durradocument.document is not None:
            return self.generateDocument()
        else:
            return 'document is not set'

    def commitDocumentCurrentVersion(self, extramsg=None):
        if self.durradocument.document is not None:
            return self.commitDocument(extramsg)
        else:
            return 'document is not set'



    def generateDocumentNewMinjorVersion(self):
        if self.durradocument.document is not None:
            self.newMinjorVersion()
            return self.generateDocument()
        else:
            return 'document is not set'

    def commitDocumentNewMinjorVersion(self, extramsg=None):
        if self.durradocument.document is not None:
            self.newMinjorVersion()
            return self.commitDocument(extramsg)
        else:
            return 'document is not set'



    def generateDocumentNewMajorVersion(self):
        if self.durradocument.document is not None:
            self.newMajorVersion()
            return self.generateDocument()
        else:
            return 'document is not set'

    def commitDocumentNewMajorVersion(self, extramsg=None):
        if self.durradocument.document is not None:
            self.newMajorVersion()
            return self.commitDocument(extramsg)
        else:
            return 'document is not set'



    def generateDocumentNewPatchedVersion(self):
        if self.durradocument.document is not None:
            self.newPatchedVersion()
            return self.generateDocument()
        else:
            return 'document is not set'

    def commitDocumentNewPatchedVersion(self, extramsg=None):
        if self.durradocument.document is not None:
            self.newPatchedVersion()
            return self.commitDocument(extramsg)
        else:
            return 'document is not set'

