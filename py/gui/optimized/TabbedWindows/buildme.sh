#!/bin/sh
make distclean
qmake $@
make -Bj20
