ifndef MINGW
	CC=gcc
	INCLUDES=$(shell pkg-config purple --cflags)
	LIBS=$(shell pkg-config purple --libs)
	DEFINES+=
	OBJDIR:=obj
	LIBSUFFIX=so
	PYMODULE_SUFFIX:=$(LIBSUFFIX)
	EXEC=yobot
	TPL=contrib/tpl.o
	PYHDR=-I/usr/include/python2.5
	PYLIB=
	PROTOCLIENT_LIB=libyobotprotoclient.so
	CLEAN_EXTRA=$(TPL)
	MODULES=
else
	CC=i586-mingw32msvc-gcc
	OBJDIR=obj/win32
	WROOT=/sources/winpurple
	WHIER=$(WROOT)/win32-dev
	INCLUDES=-I$(WROOT)/libpurple -I$(WHIER)/include/glib-2.0 \
		 -I$(WHIER)/include -I$(WHIER)/lib/glib-2.0/include
	LIBS=-L$(WHIER)/bin -L$(WHIER)/lib -L$(WROOT)/libpurple \
	     -Lcontrib/win  -lglib-2.0 -lpurple.dll -ltpl -lws2_32
	LIBSUFFIX=dll
	PYMODULE_SUFFIX=pyd
	EXEC=yobot.exe
	TPL=contrib/tpl.dll
	PYHDR=-I$(WROOT)/Python26/include
	PYLIB=-L$(WROOT)/Python26/libs -lpython26 -lws2_32
	PROTOCLIENT_LIB=yobotprotoclient.dll
	CLEAN_EXTRA=
	#first build the hack dll
	OBJS=win32/yobot_win32.c
endif

MODULES+=yobot_ui yobot_uiops yobot_conversation protoclient yobot_blist yobot_log
OBJS+=$(addprefix $(OBJDIR)/, $(addsuffix .o, $(MODULES)))
INCLUDES+=-I$(shell pwd)
CFLAGS=-Wall -ggdb3 $(DEFINES) $(INCLUDES)
PYMODULE=py/_yobotproto.$(PYMODULE_SUFFIX)
PYMODULE_SRC=py/yobotproto_wrap.c
PYMODULE_PY=py/yobotproto.py

$(OBJDIR)/%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

all: $(EXEC)

$(TPL):
	$(MAKE) -C contrib

$(EXEC): main.c $(OBJS) $(PROTOCLIENT_LIB) $(SUPPORT)
	$(CC) $(CFLAGS) $^ -o $@ $(LIBS)

$(PROTOCLIENT_LIB): protoclient.c $(TPL)
	$(CC) $(CFLAGS) -shared -fpic $^ -o $@ $(LIBS)

#SWIG stuff
$(PYMODULE_SRC): yobotproto.i
	swig -python -o $@ $^

$(PYMODULE): $(PYMODULE_SRC) $(PROTOCLIENT_LIB)
	$(CC) $(CFLAGS) $(PYHDR) -I. -shared -fpic $^ -o $@ $(PYLIB)

$(PYMODULE_PY): $(PYMODULE)

swig: $(PYMODULE) $(PYMODULE_PY)
#end SWIG

clean:
	rm -f $(OBJS) $(PYMODULE) $(PROTOCLIENT_LIB) $(PYMODULE_SRC) \
		$(EXEC) $(CLEAN_EXTRA) $(PYMODULE_PY)

ifdef MINGW
include win32/defs.mak
endif
