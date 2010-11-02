#!/usr/bin/env python
import os
import sipconfig
from PyQt4 import pyqtconfig
import sys
from optparse import OptionParser
parser = OptionParser()
parser.add_option("-d", "--build-dir", dest="build_dir",
        default=os.path.join(os.curdir, "build"))
parser.add_option("-I", "--include", dest="includes", action="append",
        default=[os.curdir])
parser.add_option("-l", "--lib",  dest="lib")
parser.add_option("-C", "--sipdir", dest="sipdir",
        help="where to find the sip files to build", default=".")
parser.add_option("-m", "--makefile-only", dest="makefile_only",
    action="store_true", default=False)
parser.add_option("-o", "--dest-dir", dest="dest_dir",
        help="where to place the generated module", default=".")

options, _ = parser.parse_args()
if not options.lib:
    raise ValueError("Must specify library to link with!")

if not os.path.exists(options.build_dir):
    os.mkdir(options.build_dir)

build_file = os.path.join(options.build_dir, "build.sipbuild")

config = pyqtconfig.Configuration()
qt_sip_flags = config.pyqt_sip_flags
cmd = " ".join([config.sip_bin,
    "-I", config.pyqt_sip_dir,
    " ".join(["-I " + str(s) for s in options.includes if s]),
    "-b", build_file,
    "-c", options.build_dir,
    qt_sip_flags, os.path.join(options.sipdir, "tabbedwindows.sip")])
if not options.makefile_only:
    print "Invoking: ", cmd
    os.system(cmd)
makefile = pyqtconfig.QtGuiModuleMakefile(
        configuration = config,
        build_file = os.path.abspath(build_file),
        dir = options.build_dir,
        install_dir = options.dest_dir
        )
makefile.extra_include_dirs = [os.path.abspath(s) for s in options.includes if
        s]
#print dir(makefile)
makefile.LIBS.append(os.path.abspath(options.lib))
print makefile.LIBS.as_list()
makefile.generate()
