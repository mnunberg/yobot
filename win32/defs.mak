SUPPORT=$(SUPPORT_DIR)/yobot_win32.o
$(SUPPORT): $(SUPPORT_DIR)/yobot_win32.c
	$(CC) $(CFLAGS) -c $^ -o $@
