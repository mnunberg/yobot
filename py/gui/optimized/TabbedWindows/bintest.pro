TARGET=testrun
TEMPLATE=app
SOURCES += test.cpp \
	testwidget.cpp
HEADERS += testwidget.h
DEFINES += TESTLIB
LIBS += -L. -lTabbedWindows
