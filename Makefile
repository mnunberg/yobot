ifndef MINGW
	CC=gcc
	INCLUDES=$(shell pkg-config purple --cflags)
	LIBS=$(shell pkg-config purple --libs)
	DEFINES+=
	OBJDIR:=obj
	LIBPREFIX=lib
	LIBSUFFIX=so
	PYMODULE_SUFFIX:=$(LIBSUFFIX)
	EXEC=yobot
	TPL=contrib/tpl.a
	PYHDR=-I/usr/include/python2.5
	PYLIB=
	CLEAN_EXTRA=$(TPL)
	PROTCLIENT_EXTRA_LIBS=
	MODULES=
	LOGGER_EXTRA_LIBS=-lcurses
else
	BINPREFIX=i586-mingw32msvc-
	CC=$(BINPREFIX)gcc
	AR=$(BINPREFIX)ar
	LD=$(BINPREFIX)ld
	OBJDIR=obj/win32
	WROOT=/sources/winpurple
	WHIER=$(WROOT)/win32-dev
	INCLUDES=-I$(WROOT)/libpurple -I$(WHIER)/include/glib-2.0 \
		 -I$(WHIER)/include -I$(WHIER)/lib/glib-2.0/include
	LIBS=-L$(WHIER)/bin -L$(WHIER)/lib -L$(WROOT)/libpurple \
	     -lglib-2.0 -lpurple.dll -lws2_32
	LIBPREFIX=
	LIBSUFFIX=dll
	PYMODULE_SUFFIX=pyd
	EXEC=yobot.exe
	TPL=contrib/tpl.dll.a
	PROTOCLIENT_EXTRA_LIBS=-lws2_32
	SUPPORT=$(wildcard win32/*.c)
	PYHDR=-I$(WROOT)/Python26/include
	PYLIB=-L$(WROOT)/Python26/libs -lpython26 -lws2_32
	CLEAN_EXTRA=$(TPL)
	LOGGER_EXTRA_LIBS=
	#first build the hack dl
endif

ifdef DARWIN
	LIBSUFFIX=dylib
	PYLIB=$(shell python2.6-config --ldflags)
	OBJDIR=obj/osx
	PYHDR=$(shell python2.6-config --cflags)
endif

PROTOCLIENT_LIB=$(LIBPREFIX)yobotprotoclient.$(LIBSUFFIX)
MODULES+=yobot_ui yobot_uiops yobot_conversation yobot_blist yobot_log yobot_request yobotutil
OBJS+=$(addprefix $(OBJDIR)/, $(addsuffix .o, $(MODULES)))
INCLUDES+=-I$(shell pwd)
CFLAGS+=-Wall -ggdb3 $(DEFINES) $(INCLUDES)
PYMODULE=py/_yobotproto.$(PYMODULE_SUFFIX)
PYMODULE_SRC=py/yobotproto_wrap.c
PYMODULE_PY=py/yobotproto.py

$(OBJDIR)/%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

all: $(EXEC) $(PYMODULE) 

$(EXEC): main.c $(OBJS) $(SUPPORT) $(PROTOCLIENT_LIB)
	$(CC) $(CFLAGS) $^ -o $@ $(LIBS) $(LOGGER_EXTRA_LIBS)

.EXPORT_ALL_VARIABLES: $(TPL)
$(TPL):
	$(MAKE) -C contrib
$(PROTOCLIENT_LIB): protoclient.c yobot_log.c $(TPL)
	$(CC) $(CFLAGS) -DTPL_NOLIB -DPROTOLIB -shared -fpic protoclient.c yobot_log.c -o $@ \
		$(TPL) $(PROTOCLIENT_EXTRA_LIBS) $(LOGGER_EXTRA_LIBS)

#SWIG stuff
$(PYMODULE_SRC): yobotproto.i
	swig -python -o $@ $^

$(PYMODULE): $(PYMODULE_SRC) $(PROTOCLIENT_LIB)
	$(CC) $(CFLAGS) $(PYHDR) -I. -shared -fpic $^ -o $@ $(PYLIB)

$(PYMODULE_PY): $(PYMODULE)

#swig: $(PYMODULE) $(PYMODULE_PY)
#end SWIG

clean:
	rm -f $(OBJS) $(PYMODULE) $(PROTOCLIENT_LIB) $(PYMODULE_SRC) \
		$(EXEC) $(CLEAN_EXTRA) $(PYMODULE_PY)
	$(MAKE) -C contrib clean
