#!/usr/bin/env python
import os
import sipconfig
from PyQt4 import pyqtconfig

build_file = "tabbedwindows.sbf"
config = pyqtconfig.Configuration()
qt_sip_flags = config.pyqt_sip_flags
cmd = " ".join([config.sip_bin, "-c", ".", "-b", build_file, "-I",
    config.pyqt_sip_dir, qt_sip_flags, "-j", "9", "tabbedwindows.sip"])
print "Invoking: ", cmd
os.system(cmd)

installs = []
installs.append(["tabbedwindows.sip", os.path.join(config.default_sip_dir,
    "tabbedwindows")])
makefile = pyqtconfig.QtGuiModuleMakefile(
        configuration = config,
        build_file = build_file,
        installs = installs
        )
makefile.LFLAGS.append("-L../")
makefile.extra_libs=["TabbedWindows"]
makefile.generate()
