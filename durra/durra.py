try:
    from krita import *
    CONTEXT_KRITA = True
    Krita = Krita  # to stop Eric ide complaining about unknown Krita
    EXTENSION = krita.Extension

except ImportError:  # script being run in testing environment without Krita
    CONTEXT_KRITA = False
    EXTENSION = QWidget

from .durraext import DURRAExt

if CONTEXT_KRITA:
    # And add the extension to Krita's list of extensions:
    app = Krita.instance()
    extension = DURRAExt(parent=app)  # instantiate your class
    app.addExtension(extension)