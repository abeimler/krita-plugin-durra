import os
import sys
import io

import re
from datetime import datetime
import math

try:
    from . import markdown2
except:
    import markdown2


class DURRADocument(object):
    def __init__(self):
        self.title = ""
        self.subject = ""
        self.description=""
        self.categories = []
        self.duration_sec = 0
        self.keywords = []
        self.date = datetime.now()
        self.authorname = "Unknown"
        self.authoremail = ""
        self.license = ""
        self.revisionstr = "0"

        self.tags = []
        self.points = None
        self.prio = 0

        self.versionstr = "0.0.0"
        self.releaseversion = False

    def getKeywordsStr(self):
        return ";".join(self.keywords)

    def loadVersionFromWorkdir(self, workdir):
        filename = ""
        if workdir != "":
            filename = os.path.join(os.path.normpath(workdir), 'VERSION')
            if os.path.isfile(filename):
                f = open(filename, "r")
                self.versionstr = f.read()
                f.close()
    
    @staticmethod
    def getTrelloTitle(categories, title, tags, timeentry, points, hashtags, prio):
        """Category | Card Title [tag] {time-entry} |points| #hashtag !"""
        category_str = '| '.join(categories)

        tags_str=""
        for t in tags:
            tags_str = tags_str + "[{0}]".format(t)
        if tags_str != "":
            tags_str = " " + tags_str

        hashtag_str=""
        for ht in hashtags:
            hashtag_str = hashtag_str + "#{0}".format(ht) + " "
        if hashtag_str != "":
            hashtag_str = " " + hashtag_str

        timeentry_str = ""
        if timeentry:
            timeentry_str  = " {" + timeentry + "}"

        points_str = ""
        if points:
            points_str  = " |{0}|".format(points)

        prio_str=""
        for i in range(prio):
            prio_str = prio_str+ "!"
        if prio_str != "":
            prio_str = " " + prio_str

        if category_str:
            title = " " + title

        return category_str + title + timeentry_str + points_str + tags_str + hashtag_str + prio_str


    def genTitleFile(self, workdir):
        filename = os.path.join(os.path.normpath(workdir), 'TITLE')
        file = open(filename, "w+")
        file.write(self.title)
        file.close()
        return filename

    def genKeywordFile(self, workdir):
        filename = os.path.join(os.path.normpath(workdir), 'KEYWORDS')
        file = open(filename, "w+")
        file.write(' '.join(self.keywords))
        file.close()
        return filename
    
    def getDescriptionContent(self):
        output = io.StringIO()

        if self.subject:
            output.write("\n### " + self.subject + "\n\n")
        output.write(self.description)
        
        ret = output.getvalue()
        output.close()
        return ret

    def getDescriptionContentBBCode(self):
        return self.markdown_to_bbcode(self.getDescriptionContent())

    def getDescriptionContentHTML(self):
        return self.markdown_to_html(self.getDescriptionContent())

    
    def genDescriptionFile(self, workdir):
        filename = os.path.join(os.path.normpath(workdir), 'DESCRIPTION.md')
        file = open(filename, "w+")
        file.write(self.getDescriptionContent())
        file.close()
        return filename
    
    def genDescriptionFileBBCode(self, workdir):
        filename = os.path.join(os.path.normpath(workdir), 'DESCRIPTION.bbcode')
        file = open(filename, "w+")
        file.write(self.getDescriptionContentBBCode())
        file.close()
        return filename

    def genDescriptionFileHTML(self, workdir):
        filename = os.path.join(os.path.normpath(workdir), 'DESCRIPTION.html')
        file = open(filename, "w+")
        file.write(self.getDescriptionContentHTML())
        file.close()
        return filename

    def getReadmeContent(self):
        dura = self.getDurationHours()
        dura_text = self.getDurationText()

        newkeywords=[]
        for key in self.keywords:
            key = key.replace(' ', '_')
            newkeywords.append(key)

        output = io.StringIO()

        title = self.getTrelloTitle(self.categories, self.title, self.tags, dura, self.points, newkeywords, self.prio)

        output.write("# " + title + "\n")
        output.write("\n")

        output.write("## Description\n")
        output.write("\n")
        output.write(self.getDescriptionContent())
        output.write("\n")
        output.write("\n")

        output.write("## More Infos\n")
        output.write("\n")
        output.write("Date: " + self.date.strftime("%d.%m.%Y") + "  \n")
        output.write("Duration: " + dura_text + "  \n")
        output.write("  \n")
        output.write("  \n")

        output.write("## Credits\n")
        output.write("\n")
        output.write(self.getLicenseContent())
        output.write("  \n")
        output.write("  \n")

        if len(newkeywords) > 0:
            output.write("## Keywords\n")
            output.write(' '.join(newkeywords) + "  \n")
            output.write("  \n")
            output.write("  \n")


            newkeywords_hashtags_str=""
            for ht in newkeywords:
                newkeywords_hashtags_str = newkeywords_hashtags_str + "#{0}".format(ht) + " "
            output.write("## Keywords (Hashtags)\n")
            output.write(newkeywords_hashtags_str + "  \n")
            output.write("  \n")
            output.write("  \n")

        ret = output.getvalue()
        output.close()
        return ret

    def genReadmeFile(self, workdir):
        filename = os.path.join(os.path.normpath(workdir), 'README.md')
        file = open(filename, "w+")
        file.write(self.getReadmeContent())
        file.close()
        return filename

    def getLicenseContent(self):
        authoremail_output = ''
        if self.authoremail != "":
            authoremail_output = ' ' + '<' + self.authoremail + '>'

        output = io.StringIO()

        output.write(self.license + "  \n")
        output.write("Art by " + self.authorname + authoremail_output + "\n")

        ret = output.getvalue()
        output.close()
        return ret

    def genLicenseFile(self, workdir):
        filename = os.path.join(os.path.normpath(workdir), 'LICENSE')
        file = open(filename, "w+")
        file.write(self.getLicenseContent())
        file.close()
        return filename
    
    def setNewVersion(self, newversion, revision=None):
        versionarr = self.getNewVersionArr(newversion, revision)
        self.versionstr = self.ver_str(versionarr)
        return self.versionstr
    
    def setNewReleaseVersion(self, newversion):
        versionarr = self.getNewVersionArr(newversion, None)
        self.versionstr = self.ver_str(versionarr)
        self.releaseversion = True
        return self.versionstr
    
    def setNewVersionRevision(self, revision):
        versionarr = self.getVERSIONArr()
        versionarr = self.getNewVersionArr(versionarr, revision)
        self.versionstr = self.ver_str(versionarr)
        return self.versionstr
    
    def getVersionContent(self):
        output = io.StringIO()

        output.write(self.versionstr)

        ret = output.getvalue()
        output.close()
        return ret

    def genVersionFile(self, workdir):
        filename = os.path.join(os.path.normpath(workdir), 'VERSION')
        file = open(filename, "w+")
        file.write(self.getVersionContent())
        file.close()
        return filename
    
    def makeMetaFiles(self, workdir):
        filenameTitle = self.genTitleFile(workdir)
        filenameDescription = self.genDescriptionFile(workdir)
        filenameDescriptionBBCode = self.genDescriptionFileBBCode(workdir)
        filenameDescriptionHTML = self.genDescriptionFileHTML(workdir)
        filenameKeyword = self.genKeywordFile(workdir)
        filenameReadme = self.genReadmeFile(workdir)
        filenameLicense = self.genLicenseFile(workdir)
        filenameVersion = self.genVersionFile(workdir)

        files = [filenameTitle, 
                 filenameDescription, filenameDescriptionBBCode, filenameDescriptionHTML, 
                 filenameKeyword,
                 filenameReadme, filenameLicense, filenameVersion]

        return files

        
    


    def getVERSIONArr(self):
        return self.ver_arr(self.versionstr)

    def getNewVersion(self, newversion=None, revision=None):
        return self.ver_str(self.getNewVersionArr(newversion, revision))
    
    def getNewVersionRevision(self, revision=None):
        return self.ver_str(self.getNewVersionArr(None, revision))
    
    def getNewVersionArr(self, newversion=None, revision=None):
        versionarr = self.getVERSIONArr()

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

    def setNewMajorVersion(self):
        versionarr = self.getVERSIONArr()
        newversion = versionarr
        newversion[0] = versionarr[0] + 1
        newversion[1] = 0
        newversion[2] = 0
        return self.setNewReleaseVersion(newversion)

    def setNewMinjorVersion(self):
        versionarr = self.getVERSIONArr()
        newversion = versionarr
        newversion[0] = versionarr[0]
        newversion[1] = versionarr[1] + 1
        newversion[2] = 0
        return self.setNewReleaseVersion(newversion)

    def setNewPatchVersion(self):
        versionarr = self.getVERSIONArr()
        newversion = versionarr
        newversion[0] = versionarr[0]
        newversion[1] = versionarr[1]
        newversion[2] = versionarr[2] + 1
        return self.setNewReleaseVersion(newversion)

    def setNewPatchRevisionVersion(self, revision):
        newversion = self.getVERSIONArr()
        return self.setNewVersion(newversion, revision)

    def getRevisionVersion(self):
        return "0." + self.revisionstr + ".0"

    def setRevisionVersion(self):
        self.versionstr = "0." + self.revisionstr + ".0"
        return self.versionstr

    def getDurationText(self):
        timeElapsed = int(self.duration_sec) if self.duration_sec != 0 else 0
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
    
    def getDurationHours(self):
        timeElapsed = int(self.duration_sec) if self.duration_sec != 0 else 0
        #secondsElapsed = int(timeElapsed % 60)
        #minutesElapsed = int((timeElapsed / 60) % 60)
        #hoursElapsed = int((timeElapsed / 3600) % 24)
        #daysElapsed = int((timeElapsed / 86400) % 7)
        #weeksElapsed = int(timeElapsed / 604800)

        hoursElapsedTotal = round(timeElapsed / 3600, 2)
        if timeElapsed > 60:
            hoursElapsedTotal = round(timeElapsed / 3600)

        return "{0} hours".format(hoursElapsedTotal)


    @staticmethod
    def formatPlural(format1, format2, value):
        if value == 1:
            return format1.format(value)
        else:
            return format2.format(value)

    @staticmethod
    def ver_str(versionarr):
        return ".".join(map(str, versionarr))

    @staticmethod
    def ver_arr(versionstr):
        va = versionstr.split('.')
        return [
            int(va[0]) if len(va) >= 1 and va[0] else 0,
            int(va[1]) if len(va) >= 2 and va[1] else 0,
            int(va[2]) if len(va) >= 3 and va[2] else 0
        ]
        
    @staticmethod
    def ver_cmp(a, b):
        va = DURRADocument.ver_arr(a)
        vb = DURRADocument.ver_arr(b)

        if (va[0] == vb[0]) and (va[1] == vb[1]) and (va[2] == vb[2]):
            return 0

        if (va[0] > vb[0]):
            return 1

        if (va[1] > vb[1]):
            return 1

        if (va[2] > vb[2]):
            return 1

        return -1

    @staticmethod
    def markdown_to_html(s):
        return markdown2.markdown(s) 

    @staticmethod
    def markdown_to_bbcode(s):
        """sma/markdown_to_bbcode.py - https://gist.github.com/sma/1513929"""

        links = {}
        codes = []
        def gather_link(m):
            links[m.group(1)]=m.group(2); return ""
        def replace_link(m):
            return "[url=%s]%s[/url]" % (links[m.group(2) or m.group(1)], m.group(1))
        def gather_code(m):
            codes.append(m.group(3)); return "[code=%d]" % len(codes)
        def replace_code(m):
            return "%s" % codes[int(m.group(1)) - 1]
        
        def translate(p="%s", g=1):
            def inline(m):
                s = m.group(g)
                s = re.sub(r"(`+)(\s*)(.*?)\2\1", gather_code, s)
                s = re.sub(r"\[(.*?)\]\[(.*?)\]", replace_link, s)
                s = re.sub(r"\[(.*?)\]\((.*?)\)", "[url=\\2]\\1[/url]", s)
                s = re.sub(r"<(https?:\S+)>", "[url=\\1]\\1[/url]", s)
                s = re.sub(r"\B([*_]{2})\b(.+?)\1\B", "[b]\\2[/b]", s)
                s = re.sub(r"\B([*_])\b(.+?)\1\B", "[i]\\2[/i]", s)
                return p % s
            return inline
        
        s = re.sub(r"(?m)^\[(.*?)]:\s*(\S+).*$", gather_link, s)
        s = re.sub(r"(?m)^    (.*)$", "~[code]\\1[/code]", s)
        s = re.sub(r"(?m)^(\S.*)\n=+\s*$", translate("~[size=200][b]%s[/b][/size]"), s)
        s = re.sub(r"(?m)^(\S.*)\n-+\s*$", translate("~[size=100][b]%s[/b][/size]"), s)
        s = re.sub(r"(?m)^#\s+(.*?)\s*#*$", translate("~[size=200][b]%s[/b][/size]"), s)
        s = re.sub(r"(?m)^##\s+(.*?)\s*#*$", translate("~[size=100][b]%s[/b][/size]"), s)
        s = re.sub(r"(?m)^###\s+(.*?)\s*#*$", translate("~[b]%s[/b]"), s)
        s = re.sub(r"(?m)^> (.*)$", translate("~[quote]%s[/quote]"), s)
        s = re.sub(r"(?m)^[-+*]\s+(.*)$", translate("~[list]\n[*]%s\n[/list]"), s)
        s = re.sub(r"(?m)^\d+\.\s+(.*)$", translate("~[list=1]\n[*]%s\n[/list]"), s)
        s = re.sub(r"(?m)^((?!~).*)$", translate(), s)
        s = re.sub(r"(?m)^~\[", "[", s)
        s = re.sub(r"\[/code]\n\[code(=.*?)?]", "\n", s)
        s = re.sub(r"\[/quote]\n\[quote]", "\n", s)
        s = re.sub(r"\[/list]\n\[list(=1)?]\n", "", s)
        s = re.sub(r"(?m)\[code=(\d+)]", replace_code, s)
        
        return s
