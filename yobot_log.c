#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include "yobot_log.h"

/*Logging subsystem*/
void yobot_logger(yobot_log_level level, int line, const char *fn, const char *fmt, ...) {
	if(yobot_log_params.level > level) {
		printf("level failed");
		return;
	}
	va_list ap;
	va_start(ap, fmt);
	printf("[%s:%d] ", yobot_log_params.prefix, line);
	printf("%s: ", fn);
	vprintf(fmt, ap);
	printf("\n");
	fflush(NULL);
	va_end(ap);
}
