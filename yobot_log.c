#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include "yobot_log.h"

/*Logging subsystem*/
void yobot_logger(yobot_log_s logparams, yobot_log_level level, int line, const char *fn, const char *fmt, ...) {
	if(logparams.level > level) {
		printf("level failed");
		return;
	}
	va_list ap;
	va_start(ap, fmt);
	printf("[%s] ", logparams.prefix);
	printf("%s:%d ", fn, line);
	vprintf(fmt, ap);
	printf("\n");
	fflush(NULL);
	va_end(ap);
}
