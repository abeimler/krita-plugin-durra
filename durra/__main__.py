import os
import sys

from PyQt5 import QtGui
from PyQt5.QtCore import QStandardPaths, QSettings
from PyQt5.QtWidgets import QApplication,  QWidget,  QMessageBox, QFileDialog
from PyQt5.QtXml import QDomDocument, QDomNode

try:
    from krita import *
    CONTEXT_KRITA = True
    Krita = Krita  # to stop Eric ide complaining about unknown Krita
    EXTENSION = krita.Extension

except ImportError:  # script being run in testing environment without Krita
    CONTEXT_KRITA = False
    EXTENSION = QWidget

from durraext import DURRAExt

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
