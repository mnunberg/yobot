/*
 * yobot_log.h
 *
 *  Created on: Aug 19, 2010
 *      Author: mordy
 */

#ifndef YOBOT_LOG_H_
#define YOBOT_LOG_H_

typedef enum {
	YOBOT_LOG_DEBUG = 1,
	YOBOT_LOG_INFO,
	YOBOT_LOG_WARN,
	YOBOT_LOG_ERROR,
	YOBOT_LOG_CRIT
} yobot_log_level;

typedef struct {
	char *prefix;
	int level;
} yobot_log_s;

void yobot_logger(yobot_log_level level, int line, const char *fn, const char *fmt, ...);

#define __logwrap(level, fmt, ...) yobot_logger(level, __LINE__, __func__, fmt, ## __VA_ARGS__)
#define yobot_log_info(fmt, ...) __logwrap(YOBOT_LOG_INFO, fmt, ## __VA_ARGS__)
#define yobot_log_debug(fmt, ...) __logwrap(YOBOT_LOG_DEBUG, fmt, ## __VA_ARGS__)
#define yobot_log_warn(fmt, ...) __logwrap(YOBOT_LOG_WARN, fmt, ## __VA_ARGS__)
#define yobot_log_err(fmt, ...) __logwrap(YOBOT_LOG_ERROR, fmt, ## __VA_ARGS__)
#define yobot_log_crit(fmt, ...) __logwrap(YOBOT_LOG_CRIT, fmt, ## __VA_ARGS__)


extern yobot_log_s yobot_log_params;

#endif /* YOBOT_LOG_H_ */
