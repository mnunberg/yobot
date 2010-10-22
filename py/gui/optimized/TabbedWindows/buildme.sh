#!/bin/sh
false
make distclean
qmake
make -Bj20
