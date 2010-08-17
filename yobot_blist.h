/*
 * yobot_blist.h
 *
 *  Created on: Aug 8, 2010
 *      Author: mordy
 */

#ifndef YOBOT_BLIST_H_
#define YOBOT_BLIST_H_
#include "yobotproto.h"
typedef struct {
	char is_fallback;
	yobot_proto_event status_event;
	const char *status_message;
} yobot_status_r;

/*if acctid is 0, then a commflags and reference parameter are expected*/
void yobot_blist_send_status_change(char *user, yobot_status_r ystatus, uint32_t acctid, ...);
void yobot_blist_send_icon(PurpleBuddy *buddy, uint32_t acctid, ...);
yobot_status_r yobot_blist_get_status(PurpleStatus *status);

#endif /* YOBOT_BLIST_H_ */
