import os
import sys
from PyQt5.QtCore import QStandardPaths, QSettings
from PyQt5.QtWidgets import QApplication,  QWidget,  QMessageBox
import PyQt5.uic as uic
from PyQt5.QtXml import QDomDocument

import re
import subprocess
from datetime import datetime
#import dateutil.parser
import math


try:
    import krita
    CONTEXT_KRITA = True
    Krita = Krita  # to stop Eric ide complaining about unknown Krita
    EXTENSION = krita.Extension

except ImportError:  # script being run in testing environment without Krita
    CONTEXT_KRITA = False
    EXTENSION = QWidget

#TESTING = True
#TESTING = False


class DURRABackendExt(EXTENSION):
    PREVIEW_SCALE = 0.5

    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        self.output = ""

        # do setup stuff
        self.script_abs_path = os.path.dirname(os.path.realpath(__file__))

        app_data_location = QStandardPaths.AppDataLocation
        pykrita_directory = QStandardPaths.writableLocation(app_data_location)
        if not CONTEXT_KRITA:
            pykrita_directory = os.path.join(pykrita_directory, "krita")
        pykrita_directory = os.path.join(pykrita_directory, "pykrita")
        self.pykrita_directory = pykrita_directory

    def print(self, str):
        if str is not None:
            self.output = self.output + str

    def println(self, str):
        if str is not None:
            self.output = self.output + str + '\n'


    def formatPlural(self, format1, format2, value):
        if value == 1:
            return format1.format(value)
        else:
            return format2.format(value)

    def ver_str(self, versionarr):
        return ".".join(map(str, versionarr))

    def ver_arr(self, versionstr):
        va = versionstr.split('.')
        return [
            int(va[0]) if va[0] is not None else 0,
            int(va[1]) if va[1] is not None else 0,
            int(va[2]) if va[2] is not None else 0
        ]

    def ver_cmp(self, a, b):
        return cmp(self.ver_arr(a), self.ver_arr(b))

    def getVERSIONArr(self, filename):
        versionstr = '0.0.0'
        if os.path.exists(filename):
            file = open(filename, 'r+')
            versionstr = file.readline()
            file.close()

        return self.ver_arr(versionstr)

    def getNewVersion(self, versionarr, revision=None, newversion=None):
        if newversion is not None:
            if newversion[0] is not None:
                versionarr[0] = newversion[0]

            if newversion[1] is not None:
                versionarr[1] = newversion[1]

            if newversion[2] is not None:
                versionarr[2] = newversion[2]
            else:
                versionarr[2] = revision if revision is not None else versionarr[2]
        else:
            versionarr[2] = revision if revision is not None else versionarr[2]

        return versionarr

    def newMajorVersion(self, versionarr):
        revision = None
        newversion = versionarr
        newversion[0] = newversion[0] + 1
        newversion[1] = 0
        newversion[2] = 0
        return self.getNewVersion(versionarr, revision, newversion)

    def newMinjorVersion(self, versionarr):
        revision = 0
        newversion = versionarr
        newversion[0] = newversion[0]
        newversion[1] = newversion[1] + 1
        newversion[2] = 0
        return self.getNewVersion(versionarr, revision, newversion)

    def newPatchVersion(self, versionarr):
        newversion = versionarr
        newversion[0] = newversion[0]
        newversion[1] = newversion[1]
        newversion[2] = newversion[2] + 1
        revision = newversion[2]
        return self.getNewVersion(versionarr, revision, newversion)

    def newPatchRevisionVersion(self, versionarr, revision):
        newversion = None
        return self.getNewVersion(versionarr, revision, newversion)

    def genTitleFile(self, workdir, title):
        filename = os.path.normpath(workdir) + '/TITLE'
        file = open(filename, "w+")
        file.write(title)
        file.close()
        return filename

    def genDescriptionFile(self, workdir, description):
        filename = os.path.normpath(workdir) + '/DESCRIPTION'
        file = open(filename, "w+")
        file.write(description)
        file.close()
        return filename

    def genKeywordFile(self, workdir, keyword):
        filename = os.path.normpath(workdir) + '/KEYWORDS'
        file = open(filename, "w+")
        file.write(keyword)
        file.close()
        return filename

    def getDurationText(self, seconds):
        timeElapsed = int(seconds) if seconds != 0 else 0
        secondsElapsed = int(timeElapsed % 60)
        minutesElapsed = int((timeElapsed / 60) % 60)
        hoursElapsed = int((timeElapsed / 3600) % 24)
        daysElapsed = int((timeElapsed / 86400) % 7)
        weeksElapsed = int(timeElapsed / 604800)

        majorTimeUnit = ""
        minorTimeUnit = ""

        hoursElapsedTotal = round(timeElapsed / 3600, 2)
        if timeElapsed > 60:
            hoursElapsedTotal = round(timeElapsed / 3600)

        if weeksElapsed > 0:
            majorTimeUnit = self.formatPlural(
                "{0} week", "{0} weeks", weeksElapsed)
            minorTimeUnit = self.formatPlural(
                "{0} day", "{0} days", daysElapsed)
        elif daysElapsed > 0:
            majorTimeUnit = self.formatPlural(
                "{0} day", "{0} days", daysElapsed)
            minorTimeUnit = self.formatPlural(
                "{0} hour", "{0} hours", hoursElapsed)
        elif hoursElapsed > 0:
            majorTimeUnit = self.formatPlural(
                "{0} hour", "{0} hours", hoursElapsed)
            minorTimeUnit = self.formatPlural(
                "{0} minute", "{0} minutes", minutesElapsed)
        elif minutesElapsed > 0:
            majorTimeUnit = self.formatPlural(
                "{0} minute", "{0} minutes", minutesElapsed)
            minorTimeUnit = self.formatPlural(
                "{0} second", "{0} seconds", secondsElapsed)
        else:
            majorTimeUnit = self.formatPlural(
                "{0} second", "{0} seconds", secondsElapsed)

        dura = majorTimeUnit + " " + minorTimeUnit + \
            " (" + self.formatPlural("{0} hour",
                                     "{0} hours", hoursElapsedTotal) + ")"

        return dura

    def genReadmeFile(self, workdir, title, subject, description, datestr, editingtimestr, keyword):
        filename = os.path.normpath(workdir) + '/README.md'

        dt = datetime.strptime(datestr, "%Y-%m-%dT%H:%M:%S")

        dura = self.getDurationText(editingtimestr)

        keywords = []
        if keyword != "":
            for key in keyword.split(';'):
                key = """#""" + key
                key = key.replace(' ', '_')
                keywords.append(key)

        file = open(filename, "w+")

        file.write("""# """ + title + "\n")
        file.write("\n")
        if subject != "":
            file.write("""## """ + subject + "\n")

        file.write("\n")
        file.write(description)
        file.write("\n")
        file.write("\n")

        file.write("Date: " + dt.strftime("%d.%m.%Y") + "  \n")
        file.write("Duration: " + dura + "  \n")
        file.write("  \n")
        file.write("Keywords: " + ' '.join(keywords) + "  \n")

        file.close()
        return filename

    def genLicenseFile(self, workdir, authorname, authoremail, license):
        filename = os.path.normpath(workdir) + '/LICENSE'

        authoremail_output = ''
        if authoremail != "":
            authoremail_output = ' ' + '<' + authoremail + '>'

        file = open(filename, "w+")

        file.write(license + "  \n")
        file.write("Art by " + authorname + authoremail_output + "\n")

        file.close()
        return filename

    def genVersionFile(self, workdir, revision=None, newversion=None):
        filename = os.path.normpath(workdir) + '/VERSION'

        versionarr = self.getVERSIONArr(filename)

        versionarr = self.getNewVersion(versionarr, revision, newversion)

        versionstr = self.ver_str(versionarr)

        file = open(filename, "w+")

        file.write(versionstr)

        file.close()
        return filename

    def exportPreview(self, workdir, document):
        filename = os.path.normpath(workdir) + '/_preview.png'

        w = document.width() * self.PREVIEW_SCALE
        h = document.height() * self.PREVIEW_SCALE

        w = w if w >= 1 else 1
        h = h if h >= 1 else 1

        img = document.thumbnail(w, h)
        if img is not None:
            img.save(filename)

        return filename

    def exportImage(self, workdir, document, filename_name):
        filename = os.path.normpath(workdir) + '/' + filename_name + '.png'

        img = document.thumbnail(document.width(), document.height())
        if img is not None:
            img.save(filename)

        return filename

    def genMetaFiles(self, workdir, document, filename,
                name, title, subject, description, keyword, revision, license, 
                editingtimestr, datestr, authorname, authoremail,
                newversion=None):

        filenameTitle = self.genTitleFile(workdir, title)
        filenameDescription = self.genDescriptionFile(workdir, description)
        filenameKeyword = self.genKeywordFile(workdir, keyword)
        filenameReadme = self.genReadmeFile(workdir, title, subject, description, datestr, editingtimestr, keyword)
        filenameLicense = self.genLicenseFile(workdir, authorname, authoremail, license)
        filenameVersion = self.genVersionFile(workdir, revision, newversion)

        files = [filenameTitle, filenameDescription, filenameKeyword,
                 filenameReadme, filenameLicense, filenameVersion]

        return files

    def makeMetaFiles(self, workdir, document, filename,
                name, title, subject, description, keyword, revision, license, editingtimestr, datestr, authorname, authoremail,
                newversion=None):
        
        if filename is None or filename == "":
            self.print('filename is empty')
            return []

        files = self.genMetaFiles(workdir, document, filename,
                    name, title, subject, description, keyword, revision, license, 
                    editingtimestr, datestr, authorname, authoremail,
                    newversion)

        return files

    def makeFiles(self, workdir, document, filename,
                 name, title, subject, description, keyword, revision, license, editingtimestr, datestr, authorname, authoremail,
                 newversion=None, releaseversion=False):
        
        if filename is None or filename == "":
            self.println('filename is empty')
            return []

        files = self.genMetaFiles(workdir, document, filename,
                        name, title, subject, description, keyword, revision, license, 
                        editingtimestr, datestr, authorname, authoremail,
                        newversion)

        filenamePreview = self.exportPreview(workdir, document)
        files.append(filename)
        files.append(filenamePreview)

        if releaseversion:
            filename_name = name
            if newversion is not None:
                version = self.ver_str(newversion)
                filename_name = name + '_v' + version

            filenameImage = self.exportImage(workdir, document, filename_name)
            files.append(filenameImage)

        return files

    def getDocumentInfo(self, doc):
        title = ""
        subject = ""
        description = ""
        keyword = ""
        license = ""
        revisionstr = "0"
        editingtimestr = "0"
        authorname = ""
        datestr = "0000-00-00T00:00:00"

        if doc is not None:
            docInfo = doc.documentInfo()
            #self.print(docInfo)

            docInfoXml = QDomDocument()
            docInfoXml.setContent(docInfo)

            aboutsXml = docInfoXml.elementsByTagName("about")
            if not aboutsXml.isEmpty():
                aboutXml = aboutsXml.at(0)
                if aboutXml.isElement():
                    title = aboutXml.firstChildElement("title").text()
                    description = aboutXml.firstChildElement(
                        "description").text()
                    if description == "":
                        description = aboutXml.firstChildElement(
                            "abstract").text()

                    subject = aboutXml.firstChildElement("subject").text()
                    keyword = aboutXml.firstChildElement("keyword").text()
                    revisionstr = aboutXml.firstChildElement(
                        "editing-cycles").text()
                    editingtimestr = aboutXml.firstChildElement(
                        "editing-time").text()
                    datestr = aboutXml.firstChildElement("date").text()
                    license = aboutXml.firstChildElement("license").text()

            authorsXml = docInfoXml.elementsByTagName("author")
            if not authorsXml.isEmpty():
                authorXml = authorsXml.at(0)
                if authorXml.isElement():
                    authorname = authorXml.firstChildElement(
                        "full-name").text()
                    authoremail = authorXml.firstChildElement(
                        "email").text()
                    
                    if authoremail is None or authoremail == "":
                        authorContacts = authorXml.toElement().elementsByTagName("contact")
                        if not authorContacts.isEmpty():
                            for i in range(authorContacts.count()):
                                authorContact = authorContacts.at(i)
                                if authorContact.hasAttributes():
                                    authorContactAttributes = authorContact.attributes()
                                    for j in range(authorContactAttributes.count()):
                                        authorContactAttributeItem = authorContactAttributes.item(j)
                                        authorContactAttribute = authorContactAttributeItem.toAttr()
                                        authorContactAttributeName = authorContactAttribute.name()
                                        authorContactAttributeValue = authorContactAttribute.value()
                                        if authorContactAttributeName == "type" and authorContactAttributeValue == "email":
                                            authoremail = authorContact.toElement().text()


        return {
            "title": title,
            "subject": subject,
            "description": description,
            "keyword": keyword,
            "license": license,
            "revisionstr": revisionstr,
            "editingtimestr": editingtimestr,
            "authorname": authorname,
            "datestr": datestr,
            "authoremail": authoremail
        }

    def getVERSIONArrFromWorkdir(self, workdir):
        filename = ""
        if workdir != "":
            filename = os.path.normpath(workdir) + '/VERSION'

        return self.getVERSIONArr(filename)

    def getVERSIONArrFromDoc(self, doc):
        workdir = self.getWorkdir(doc)

        return self.getVERSIONArrFromWorkdir(workdir)

    def getWorkdir(self, doc):
        if doc is not None:
            filename = doc.fileName()

            if filename != "":
                filename_path = os.path.dirname(os.path.realpath(filename))
                work_filename_path = os.path.basename(
                    os.path.normpath(filename_path))
                workdir = filename_path
                if work_filename_path == "work":
                    workdir = os.path.dirname(os.path.realpath(filename_path))
                #workdir_basename = os.path.basename(os.path.normpath(workdir))
                return workdir

        return ""

    def runGit(self, workdir, files, msg, description="", authorname="", authoremail=""):
        output = ''

        for file in files:
            if file is not None and file != "":
                cmd = 'git add ' + "'" + file.replace("'", "'\\''") + "'"
                (out, err) = subprocess.Popen(cmd, cwd=workdir,
                                              stdout=subprocess.PIPE, shell=True).communicate()

                output = output + '$ ' + cmd + "\n"
                output = output + out.decode('UTF-8')
                self.print(err)

        cmd = 'git commit -m ' + "'" + msg.replace("'", "'\\''") + "'"
        if description != None and description != "":
            cmd = cmd + ' -m ' + "'" + description.replace("'", "'\\''").replace("\n", "\\n") + "'"
        
        if authorname != "":
            authorargstr = authorname.replace("'", "'\\''") 
            if  authoremail != "":
                authorargstr = authorname.replace("'", "'\\''") + " <" + authoremail.replace("'", "'\\''") + ">" 

            authorarg = ' --author='  + "'" + authorargstr + "'" 
            cmd = cmd + authorarg


        (out, err) = subprocess.Popen(cmd, cwd=workdir,
                                      stdout=subprocess.PIPE, shell=True).communicate()

        output = output + '$ ' + cmd + "\n"
        output = output + out.decode('UTF-8')
        
        self.println(err)

        return output



    def generateDocumentMetaFiles(self, doc, newversion=None):
        files = self._generateDocumentFiles(doc, newversion, False, True)
        output = "generate Files: " + "\n - ".join(str(x) for x in files) + "\n\n"
        return output

    def generateDocument(self, doc, newversion=None):
        files = self._generateDocumentFiles(doc, newversion, False, False)
        output = "generate Files: " + "\n - ".join(str(x) for x in files) + "\n\n"
        return output

    def generateDocumentRelease(self, doc, newversion=None):
        files = self._generateDocumentFiles(doc, newversion, True, False)
        output = "generate Files: " + "\n - ".join(str(x) for x in files) + "\n\n"
        return output

    def _generateDocumentFiles(self, doc, newversion=None, releaseversion=False, onlymetafiles=False):
        if doc is not None:
            filename = doc.fileName()

            if filename != "":
                info = self.getDocumentInfo(doc)

                if newversion is not None:
                    if newversion[2] is not None:
                        info["revisionstr"] = newversion[2]

                # @TODO edit doc info, version number
                # doc.save()

                info = self.getDocumentInfo(doc)
                name = doc.name()
                filename = doc.fileName()

                workdir = self.getWorkdir(doc)

                files = []
                if onlymetafiles:
                    files = self.makeMetaFiles(workdir, doc, filename, name,
                                        info["title"],
                                        info["subject"],
                                        info["description"],
                                        info["keyword"],
                                        info["revisionstr"],
                                        info["license"],
                                        info["editingtimestr"],
                                        info["datestr"],
                                        info["authorname"],
                                        info["authoremail"],
                                        newversion)
                else:
                    files = self.makeFiles(workdir, doc, filename, name,
                                        info["title"],
                                        info["subject"],
                                        info["description"],
                                        info["keyword"],
                                        info["revisionstr"],
                                        info["license"],
                                        info["editingtimestr"],
                                        info["datestr"],
                                        info["authorname"],
                                        info["authoremail"],
                                        newversion, releaseversion)

                return files
            else:
                self.println('filename is empty')
        else:
            self.println('document is not set')

        return []



    def commitDocument(self, doc, newversion=None, extramsg=None):
        return self._commitDocument(doc, newversion, False, False, extramsg)

    def commitDocumentMetafiles(self, doc, newversion=None, extramsg=None):
        return self._commitDocument(doc, newversion, False, True, extramsg)

    def commitDocumentRelease(self, doc, newversion=None, extramsg=None):
        return self._commitDocument(doc, newversion, True, False, extramsg)
    
    def _commitDocument(self, doc, newversion=None, releaseversion=False, onlymetafiles=False, extramsg=None):
        if doc is not None:
            filename = doc.fileName()

            if filename != "":
                files = self._generateDocumentFiles(doc, newversion, releaseversion, onlymetafiles)

                info = self.getDocumentInfo(doc)
                name = doc.name()
                filename = doc.fileName()

                workdir = self.getWorkdir(doc)
                workdir_basename = os.path.basename(os.path.normpath(workdir))

                outputfiles = "generate Files: " + "\n - ".join(str(x) for x in files) + "\n\n"

                nr = ""
                mnrs = re.search(r"^\s*(\d+)\s+\-\s+.*$", workdir_basename)
                nr = mnrs.group(1) if mnrs is not None else ""

                msg = ""
                nrstr = None
                if nr is not None and nr != "":
                    nrstr = """#""" + "{}".format(int(nr))

                if releaseversion and newversion is not None:
                    version = self.ver_str(newversion)
                    if version == "1.0.0":
                        msg = "finished " + name + " v" + version + " Closes " + nrstr
                    else:
                        msg = "new version of " + name + " v" + version
                else:
                    msg = "work on "
                    if nrstr is not None:
                        msg = msg + nrstr + " "
                    msg = msg + name

                output = self.runGit(workdir, files, msg, extramsg, info["authorname"], info["authoremail"])

                return outputfiles + output
            else:
                return 'filename is empty'
        else:
            return 'document is not set'

    def getVersionArrCurrentVersion(self, doc):
        versionarr = self.getVERSIONArrFromDoc(doc)
        docinfo = self.getDocumentInfo(doc)

        return self.newPatchRevisionVersion(versionarr, int(docinfo['revisionstr']))

    def getVersionArrNewMinjorVersion(self, doc):
        versionarr = self.getVERSIONArrFromDoc(doc)
        #docinfo = self.getDocumentInfo(doc)

        return self.newMinjorVersion(versionarr)

    def getVersionArrNewMajorVersion(self, doc):
        versionarr = self.getVERSIONArrFromDoc(doc)
        #docinfo = self.getDocumentInfo(doc)

        return self.newMajorVersion(versionarr)

    def getVersionArrNewPatchedVersion(self, doc):
        versionarr = self.getVERSIONArrFromDoc(doc)
        #docinfo = self.getDocumentInfo(doc)

        return self.newPatchVersion(versionarr)




    
    def generateDocumentMetafilesCurrentVersion(self, doc):
        if doc is not None:
            versionarr = self.getVersionArrCurrentVersion(doc)
            return self.generateDocumentMetaFiles(doc, versionarr)
        else:
            return 'document is not set'
    
    def commitDocumentMetafilesCurrentVersion(self, doc, extramsg=None):
        if doc is not None:
            versionarr = self.getVersionArrCurrentVersion(doc)
            return self.commitDocumentMetafiles(doc, versionarr, extramsg)
        else:
            return 'document is not set'

    
    def generateDocumentCurrentVersion(self, doc):
        if doc is not None:
            versionarr = self.getVersionArrCurrentVersion(doc)
            return self.generateDocument(doc, versionarr)
        else:
            return 'document is not set'

    def commitDocumentCurrentVersion(self, doc, extramsg=None):
        if doc is not None:
            versionarr = self.getVersionArrCurrentVersion(doc)
            return self.commitDocument(doc, versionarr, extramsg)
        else:
            return 'document is not set'



    def generateDocumentNewMinjorVersion(self, doc):
        if doc is not None:
            versionarr = self.getVersionArrNewMinjorVersion(doc)
            return self.generateDocumentRelease(doc, versionarr)
        else:
            return 'document is not set'

    def commitDocumentNewMinjorVersion(self, doc, extramsg=None):
        if doc is not None:
            versionarr = self.getVersionArrNewMinjorVersion(doc)
            return self.commitDocumentRelease(doc, versionarr, extramsg)
        else:
            return 'document is not set'



    def generateDocumentNewMajorVersion(self, doc):
        if doc is not None:
            versionarr = self.getVersionArrNewMajorVersion(doc)
            return self.generateDocumentRelease(doc, versionarr)
        else:
            return 'document is not set'

    def commitDocumentNewMajorVersion(self, doc, extramsg=None):
        if doc is not None:
            versionarr = self.getVersionArrNewMajorVersion(doc)
            return self.commitDocumentRelease(doc, versionarr, extramsg)
        else:
            return 'document is not set'



    def generateDocumentNewPatchedVersion(self, doc):
        if doc is not None:
            versionarr = self.getVersionArrNewPatchedVersion(doc)
            return self.generateDocumentRelease(doc, versionarr)
        else:
            return 'document is not set'

    def commitDocumentNewPatchedVersion(self, doc, commit=True, extramsg=None):
        if doc is not None:
            versionarr = self.getVersionArrNewPatchedVersion(doc)
            return self.commitDocumentRelease(doc, versionarr, extramsg)
        else:
            return 'document is not set'

