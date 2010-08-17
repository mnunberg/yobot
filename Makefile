CC=gcc
INCLUDES=$(shell pkg-config purple --cflags)
LIBS=$(shell pkg-config purple --libs)
DEFINES+= 
#DEFINES+= -DWRITE_CONTIG

CFLAGS=-Wall -g $(DEFINES) $(INCLUDES) $(LIBS)
all: yobot

chatroom.o: chatroom.c
	$(CC) $(CFLAGS) -c $^ -o $@

yobot: main.c yobot_ui.o yobot_uiops.o yobot_conversation.o protoclient.o yobot_blist.o contrib/tpl.o
	$(CC) $(CFLAGS) $^ -o $@

proto_test: protoclient.o contrib/tpl.o proto_test.c
	$(CC) $(CFLAGS) -o $@ $^
#client libs
contrib/tpl.o: contrib/tpl.c
	$(CC) $(CFLAGS) -fpic -c $^ -o $@
clientlib: libyobotclient.so

protoclient.o: protoclient.c
	$(CC)  $(CFLAGS) -fpic -c $^ -o $@

libyobotclient.so: protoclient.o contrib/tpl.c
	$(CC) $(CFLAGS)  -shared $^ -o $@


#SWIG stuff
py/yobotproto_wrap.c: yobotproto.i
	swig -I/usr/include -python -o $@ $^

py/yobotproto_wrap.o: py/yobotproto_wrap.c
	$(CC) $(CFLAGS) -c -I/usr/include/python2.5 -I. -fpic $^ -o $@

py/_yobotproto.so: py/yobotproto_wrap.o protoclient.o contrib/tpl.o
	$(CC) -shared -fpic $^ -o $@

swig: py/_yobotproto.so
#end SWIG

clean:
	rm -f *.so *.o py/*.o yobot py/yobotproto_wrap.* py/_yobotproto* py/yobotproto.py
