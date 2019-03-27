#!/usr/bin/env python
import os
import sys
from setuptools import setup, find_packages
from setup_qt import build_qt

#PyPI guide: https://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/
def read(*paths):
    """Build a file path from *paths* and return the contents."""
    with open(os.path.join(*paths), 'r') as f:
        return f.read()


# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os"], "excludes": ["tkinter"]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name='durra',
    version = '0.2.0',
    description="DURRA Krita Plugin - Developer Uses Revision contRoll for Art(-Projects)",
    long_description=(read('README.md')),
    license="MIT",
    author="Alex Beimler",
    author_email="alex-beimler@web.de",
    url="https://github.com/abeimler/krita-plugin-durra",
    platforms=["Any"],
    install_requires=[
        'argparse>=1.4.0',
        'parsedatetime>=2.4',
        'duration>=1.1.1',
        'markdown2'
        'PyQt5',
        'Qt.py',
        'GitPython'
    ],
    packages=find_packages(exclude=['gif', 'img', 'site', 'test', 'dist', 'build']),
    package_data={
        'durra': [
            '*.ui',
            '*.qrc',
            'languages/*.ts',
            'languages/*.qm',
        ],
    },
    scripts=['durra/durra.py'],
    entry_points={
        'gui_scripts': [
            'durra=durra.__main__:main',
        ],
    },
    options={
        'build_qt': {
            'packages': ['durra'],
            'bindings': 'PyQt5',           # optional ('PyQt5' is default)
            'replacement_bindings': 'Qt',  # optional (for Qt.py wrapper usage)
        }
    },
    cmdclass={
        'build_qt': build_qt,
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
)

