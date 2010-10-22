# -------------------------------------------------
# Project created by QtCreator 2010-10-21T01:07:09
# -------------------------------------------------
TARGET = TabbedWindows
TEMPLATE = app
CONFIG += debug
QMAKE_CXXFLAGS += -DTESTLIB \
    -ggdb3 \
    -Wall
SOURCES += tabbedwindows.cpp \
    dragpixmap.cpp \
    _tabbar.cpp \
    realtabwidget.cpp \
    subwindow.cpp \
    tabcontainer.cpp \
    test.cpp \
    testwidget.cpp \
    twutil.cpp
HEADERS += tabbedwindows.h \
    dragpixmap.h \
    _tabbar.h \
    realtabwidget.h \
    subwindow.h \
    tabcontainer.h \
    testwidget.h \
    twutil.h
