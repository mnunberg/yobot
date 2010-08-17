#include <stdio.h>
#include "protoclient.h"
#include "yobotproto.h"
#include <time.h>
#include <string.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <netdb.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
int main(void)
{
	signal(SIGPIPE,SIG_IGN);
	/*setup networking*/
	struct addrinfo hints;
	struct addrinfo *res;
	int s, status;

	memset(&hints,0,sizeof(struct addrinfo));

	hints.ai_family = AF_INET;
	hints.ai_socktype = SOCK_STREAM;
	hints.ai_next = NULL;

	status = getaddrinfo("localhost","7771",&hints,&res);
	if(status <0) {
		perror("");
	}

	s = socket(res->ai_family,res->ai_socktype,res->ai_protocol);
	if(s<0) {
		perror("");
	}

	status = connect(s,res->ai_addr,res->ai_addrlen);
	if(status<0) {
		perror("");
		s = -1;
	}
/*
	status =fcntl(s,F_SETFL,O_NONBLOCK);
	if(status<0) {
		perror("");
		s = -1;
	}
*/
	printf("SOCKET IS FD #%d\n",s);

	void *encoded_msg;
	yobot_protoclient_segment *decoded;


	/*msg test*/
	puts("==== MSG TEST ====");
	encoded_msg = yobot_protoclient_msg_encode(
			3,
			"to",
			"message",
			"who",
			time(NULL),
			0,
			0,
			NULL,
			YOBOT_PROTOCLIENT_TO_BUF);

	if(s >= 0) {
		yobot_protoclient_msg_encode(
					3,
					"to",
					"message",
					"who",
					time(NULL),
					YOBOT_MSG_TO_SERVER,
					PURPLE_ACCOUNT_REQUEST_AUTHORIZATION,
					&s,
					YOBOT_PROTOCLIENT_TO_FD);
	}

	printf("msg: encoded_msg: %p\n", encoded_msg);

	struct segment_r segr = yobot_proto_segfrombuf(encoded_msg);
	free(encoded_msg);
	printf("msg: segr.data: %p\n", segr.data);

	decoded = yobot_protoclient_segment_decode(segr);
	printf("MESSAGE:\n"
			"WHO: %s\n"
			"TO: %s\n"
			"MSG: %s\n",decoded->msgi->who,decoded->msgi->to,decoded->msgi->txt);

	printf("trying to free.. some stats\n");
	printf("msgi=%p, evi=%p, cmdi=%p, mkaccti=%p\n",
			decoded->msgi,decoded->evi,decoded->cmdi,decoded->mkaccti);

	yobot_protoclient_free_segment(decoded);

	/*mkacct test*/
	puts("==== MKACCT TEST ====");


	encoded_msg = yobot_protoclient_mkacct_encode(
			"mordy",
			"password",
			666,
			1,
			NULL,
			YOBOT_PROTOCLIENT_TO_BUF);

	if(s>0) {
		yobot_protoclient_mkacct_encode(
				"mordy",
				"password",
				666,
				1,
				&s,
				YOBOT_PROTOCLIENT_TO_FD);
	}


	printf("mkacct: encoded_msg: %p\n", encoded_msg);
	segr = yobot_proto_segfrombuf(encoded_msg);
	printf("mkacct: segr.data: %p\n", segr.data);
	free(encoded_msg);

	decoded = yobot_protoclient_segment_decode(segr);
	printf("mkacct: decoded: %p\n", decoded);
	printf("MKACCT:\n"
			"user: %s\npass: %s\nid: %d\nproto: %d\n",
			decoded->mkaccti->user, decoded->mkaccti->pass,
			decoded->mkaccti->yomkacct->id, decoded->mkaccti->yomkacct->improto);
	printf("trying to free.. some stats\n");
	printf("msgi=%p, evi=%p, cmdi=%p, mkaccti=%p\n",
			decoded->msgi,decoded->evi,decoded->cmdi,decoded->mkaccti);
	yobot_protoclient_free_segment(decoded);

	/*event test*/
	puts("==== EVENT TEST ====");

	char *evtxt = "Some Event Text";
	encoded_msg = yobot_protoclient_event_encode(
			YOBOT_EVENT_ACCT_REGISTERED,
			YOBOT_PURPLE_ACCOUNT,
			YOBOT_INFO,
			666,
			strlen(evtxt)+1,
			evtxt,
			NULL,
			YOBOT_PROTOCLIENT_TO_BUF);
	if(s>0) {
		yobot_protoclient_event_encode(
				YOBOT_EVENT_ACCT_REGISTERED,
				YOBOT_PURPLE_ACCOUNT,
				YOBOT_INFO,
				666,
				strlen(evtxt)+1,
				evtxt,
				&s,
				YOBOT_PROTOCLIENT_TO_FD);
	}
	printf("event: encoded_msg: %p\n", encoded_msg);
	segr = yobot_proto_segfrombuf(encoded_msg);
	free(encoded_msg);
	printf("event: segr.data: %p\n", segr.data);
	decoded = yobot_protoclient_segment_decode(segr);
	printf("event: decoded: %p\n", decoded);
	printf("EVENT:\n"
			"event=%d\npurple object=%d\nseverity=%d\nobjid=%d\ntext=%s\n",
			decoded->evi->evt->event,
			decoded->evi->evt->purple_type,
			decoded->evi->evt->event_type,
			decoded->evi->evt->obj_id,
			decoded->evi->data);
	printf("trying to free.. some stats\n");
	printf("msgi=%p, evi=%p, cmdi=%p, mkaccti=%p\n",
			decoded->msgi,decoded->evi,decoded->cmdi,decoded->mkaccti);
	yobot_protoclient_free_segment(decoded);


	/*cmd test*/
	puts("==== CMD TEST ====");
	char *room = "Linux, FreeBSD, Solaris:1";
	yobotcomm comm;
	comm.flags = 0;
	yobotcmd cmd;
	cmd.acct_id = 666;
	cmd.command = YOBOT_CMD_ROOM_JOIN;
	encoded_msg = yobot_protoclient_cmd_encode(
			&comm,
			&cmd,
			room,
			strlen(room)+1,
			NULL,
			YOBOT_PROTOCLIENT_TO_BUF);

	if(s>0) {
		yobot_protoclient_cmd_encode(
				&comm,
				&cmd,
				room,
				strlen(room)+1,
				&s,
				YOBOT_PROTOCLIENT_TO_FD);
	}
	printf("cmd: encoded_msg: %p\n", encoded_msg);
	segr = yobot_proto_segfrombuf(encoded_msg);
	free(encoded_msg);
	printf("cmd: segr.data: %p\n", segr.data);
	decoded = yobot_protoclient_segment_decode(segr);
	printf("cmd: decoded: %p\n", decoded);

	printf("COMMAND:\nflags=%d\nacct id=%d\ncommand=%d\ndata=%s\n",
			decoded->comm->flags,
			decoded->cmdi->cmd->acct_id,
			decoded->cmdi->cmd->command,
			decoded->cmdi->data);

	printf("trying to free.. some stats\n");
	printf("msgi=%p, evi=%p, cmdi=%p, mkaccti=%p\n",
			decoded->msgi,decoded->evi,decoded->cmdi,decoded->mkaccti);
	yobot_protoclient_free_segment(decoded);

	/*error checking*/
	puts("==== ERROR CHECKING ====");
	puts("passing random unallocated buf to decoded()");
	void *badbuf;
	badbuf=sbrk(0) + 666;
	yobot_proto_segfrombuf(badbuf);
	puts("passing insufficiently sized buf to decode()");
	badbuf = malloc(1);
	yobot_proto_segfrombuf(badbuf);
	free(badbuf);
	puts("passing NULL buffer to decode()");
	badbuf = NULL;
	yobot_proto_segfrombuf(badbuf);

	/*socket handler...*/
	/*
	puts("=== SOCKET DATA ====");
	if(s>0) {
		struct pollfd pl;
		pl.events = POLLIN;
		pl.fd = s;
		poll(&pl,1,-1);

		char buf[1024];
		int nread=0;
		while((nread=read(s,buf,1024))>0) {
			write(STDOUT_FILENO,buf,nread);
		}
		close(s);
	}
	*/
	return 0;
}
