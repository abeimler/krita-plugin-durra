import os
import sys
import io
import subprocess

from datetime import datetime

from PyQt5.QtXml import QDomDocument

from .durradocument import DURRADocument

class DURRADocumentKrita(DURRADocument):
    PREVIEW_SCALE = 0.5

    def __init__(self):
        super().__init__()

        self._document = None
        self._filename_kra = ""
        self._filename_name = ""

        self.revisionstr = ""

    def getKritaDocument(self):
        return self.document

    def getFilenameKra(self):
        return self._filename_kra

    def getFilenameBaseName(self):
        return self._filename_name
    
    def exportPreview(self, workdir):
        if not self._document:
            return "";

        filename = os.path.join(os.path.normpath(workdir), '_preview.png')

        w = self._document.width() * self.PREVIEW_SCALE
        h = self._document.height() * self.PREVIEW_SCALE

        w = w if w >= 1 else 1
        h = h if h >= 1 else 1

        img = self.document.thumbnail(w, h)
        if img:
            img.save(filename)

        return filename

    def exportImage(self, workdir, name):
        if not self._document:
            return "";
        
        filename = os.path.join(os.path.normpath(workdir), name + '.png')

        img = self._document.thumbnail(self._document.width(), self._document.height())
        if img:
            img.save(filename)

        return filename

    def makeFiles(self, workdir):
        files = self.makeMetaFiles(workdir)

        filenamePreview = self.exportPreview(workdir)
        files.append(filenamePreview)

        if self.releaseversion:
            newfilename_name = self._filename_name
            if self.isnewversion is not None:
                newfilename_name = self._filename_name + '_v' + self.versionstr

            filenameImage = self.exportImage(workdir, newfilename_name)
            files.append(filenameImage)

        return files


    def loadDocument(self, document):
        self._document = document
        info = self.getDocumentInfoFromDocument(self._document)

        self._filename_kra = self._document.fileName()
        self._filename_name = os.path.splitext(self._filename_kra)[0]

        self.title = info['title']
        self.subject = info['subject']
        self.categories = [info['subject']]
        self.description = info['info.description']
        self.keywords = info['keyword'].split(';')
        self.license = info['license']
        self.duration_sec = int(info['editingtimestr'])
        self.authorname = info['authorname']
        self.date = datetime.strptime(info['datestr'], "%Y-%m-%dT%H:%M:%S")
        self.authoremail = info['authoremail']
        self.revisionstr = info['revisionstr']

        newversionstr = "0." + self.revisionstr + ".0"
        if self.ver_cmp(newversionstr, self.versionstr) > 0:
            self.versionstr = newversionstr

    def getDocumentInfo(self):
        return self.getDocumentInfoFromDocument(self._document)
    
    @staticmethod
    def getDocumentInfoFromDocument(document):
        title = ""
        subject = ""
        description = ""
        keyword = ""
        license = ""
        revisionstr = "0"
        editingtimestr = "0"
        authorname = ""
        datestr = "0000-00-00T00:00:00"

        if document is not None:
            docInfo = document.documentInfo()

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