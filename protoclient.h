/*
 * protoclient.h
 *
 *  Created on: Jul 16, 2010
 *      Author: mordy
 */

#ifndef PROTOCLIENT_H_
#define PROTOCLIENT_H_

#include "yobotproto.h"
typedef enum {
	YOBOT_PROTOCLIENT_TO_FD,
	YOBOT_PROTOCLIENT_TO_BUF,
} yobot_protoclient_output;
typedef enum {
	YOBOT_PROTOCLIENT_YCMDI,
	YOBOT_PROTOCLIENT_YMSGI,
	YOBOT_PROTOCLIENT_YEVTI,
	YOBOT_PROTOCLIENT_YMKACCTI,
	YOBOT_PROTOCLIENT_CMD_SIMPLE,
} yobot_protoclient_type;
typedef struct {
	yobot_protoclient_type struct_type;
	yobotcomm *comm;
	yobotcmd_internal *cmdi;
	yobotmsg_internal *msgi;
	yobotevent_internal *evi;
	yobotmkacct_internal *mkaccti;
	const void *rawdata; /*to overcome swig limitations of automatically casting char as str*/
} yobot_protoclient_segment;

struct segment_r {
	long len;
	void *data;
	int read_return;
};

/*for the encoding functions*/
struct yobot_eventinfo {
	yobot_proto_flags commflags;
	uint32_t reference;
	yobot_proto_event event;
	yobot_proto_purple_type purple_type;
	uint32_t acctid;
	yobot_proto_evtype severity;
	const char *data;
	size_t len;
};

struct yobot_msginfo {
	yobot_proto_flags commflags;
	uint32_t reference;
	PurpleMessageFlags purple_flags;
	uint32_t acctid;
	uint32_t msgtime;
	const char *who;
	const char *to;
	const char *txt;
};

struct yobot_cmdinfo {
	yobot_proto_flags commflags;
	yobot_proto_cmd command;
	uint32_t reference;
	uint32_t acctid;
	const char *data;
	size_t len;
};

struct yobot_mkacctinfo {
	yobot_proto_flags commflags;
	uint32_t reference;
	const char *user;
	const char *password;
	uint32_t acctid;
	yobot_proto_improto improto;
};

/*functions that encode data*/

void *yobot_proto_segment_encode(yobot_proto_model_internal *model, void *output,
		yobot_protoclient_output out_type);

void *yobot_protoclient_comm_encode(yobotcomm *comm, const char *data, uint32_t len,
		void *output, yobot_protoclient_output out_type);

void *yobot_protoclient_cmd_encode(struct yobot_cmdinfo info, void *output, yobot_protoclient_output out_type);
void *yobot_protoclient_mkacct_encode(struct yobot_mkacctinfo info, void *output, yobot_protoclient_output out_type);
void *yobot_protoclient_msg_encode(struct yobot_msginfo info, void *output, yobot_protoclient_output out_type);
void *yobot_protoclient_event_encode(struct yobot_eventinfo info, void *output, yobot_protoclient_output out_type);

/*functions that unpack data*/
yobot_protoclient_segment *yobot_protoclient_segment_decode(struct segment_r seginfo);
yobot_protoclient_segment *yobot_protoclient_segment_decode_from_buf(
		char *buf, int len);

/*functions that get data*/
struct segment_r yobot_proto_read_segment(void *input);
struct segment_r yobot_proto_segfrombuf(void *buf);


/*some hacks for swig*/
int yobot_protoclient_getsegsize(void *buf);

/*free*/
void yobot_protoclient_free_segment(yobot_protoclient_segment *seg);


/*init logger*/
void yobot_proto_setlogger(char *prefix);

#endif /*PROTOCLIENT_H_*/
