ifndef MINGW
CFLAGS+=-fpic
all: tpl.a
tpl.a: tpl.o
	$(AR) rcs $@ $^
clean:
	rm -f tpl.a tpl.o
else
all: tpl.dll.a

tpl.dll.a: tpl.win.o mmap.win.o
	$(AR) rcs $@ $^

tpl.win.o: tpl.c
	$(CC) $(CFLAGS) -c -DTPL_NOLIB $^ -o $@
mmap.win.o: win/mmap.c
	$(CC) $(CFLAGS) -c $^ -o $@

clean:
	rm -f tpl.dll.a tpl.win.o mmap.win.o
endif
