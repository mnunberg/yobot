#include "yobotproto.h"
#include <unistd.h>
#include <string.h>
#include "contrib/tpl.h"
#include <assert.h>
#include "yobotutil.h"
#include "protoclient.h"
#include "yobot_log.h"
#include <errno.h>

#ifdef WIN32
#define _WIN32_WINNT 0x0501
	#include <winsock2.h>
	#include <ws2tcpip.h>
	#define EWOULDBLOCK WSAEWOULDBLOCK
	#include <windows.h>
	#include <winbase.h>
	#include <memory.h>
	#define usleep Sleep
#else
	#include <arpa/inet.h>
	#include <sys/socket.h>
	#include <netinet/in.h>
	#include <netdb.h>
	#include <fcntl.h>
	extern tpl_hook_t tpl_hook;
	typedef struct sockaddr_storage xsockaddr_storage;
#endif

#define USE_TPL

/*for logging*/
yobot_log_s yobotproto_log_params = {
		"Yobot Proto",
		1
};
static char* logprefix = NULL;
void yobot_proto_setlogger(char *prefix) {
	if(prefix && !logprefix) {
		logprefix = malloc(32);
		memset(logprefix, 0, 32);
		strncat(logprefix, prefix, 32);
		strncat(logprefix, "(proto)", 32-strlen(logprefix));
		yobotproto_log_params.prefix = logprefix;
	}
}
/*finally, make sure we don't use the main logging facilities*/
#undef yobot_log_crit
#undef yobot_log_debug
#undef yobot_log_err
#undef yobot_log_info
#undef yobot_log_warn

/*these functions free data structures*/
static void free_yobotmkacct_internal(yobotmkacct_internal *ymkaccti);
static void free_yobotcmd_internal(yobotcmd_internal *yci);
static void free_yobotevent_internal(yobotevent_internal *p);
static void free_yobotmsg_internal(yobotmsg_internal *p);


ssize_t (*read_data)(int, void *, size_t);
struct segment_r (*yobot_proto_get_segment)(void *input);

int yobot_protoclient_getsegsize(void *buf) {
	return ntohs(*(uint16_t*)buf) + 2;
}

ssize_t _read_data(int fd, void *buf, size_t count) {
	puts(__func__);
	if(recv(fd, buf, count, 0)<count) {
//	if(read(fd,buf,count)<count) {
		return 0;
	}
	return 1;
}


struct segment_r yobot_proto_segfrombuf(void *buf) {
	struct segment_r ret;
	ret.len = 0;
	ret.data = NULL;
	/*get a short*/
	/*first do some checking.. at the very least, let's ensure
	 * that we won't segfault here. we'll most likely get garbage,
	 * but we should ensure that buf is not NULL and that it's at
	 * least len+2 bytes before the end of the memory segment..
	 */
#ifndef WIN32
	extern char edata, end;
	void *_end = sbrk(0);
	if(buf+2 > _end || buf == NULL || (void*)&end > buf) {
		yobotproto_log_err("invalid buffer! starts at %p but can only read from %p until %p",
				buf,&edata,_end); goto err;
		}
#endif

	uint16_t len = ntohs(*(uint16_t*)buf);
	if(len >= YOBOT_MAX_COMMSIZE) {
		yobotproto_log_err("sanity check failed! len is %d",len);
		goto err;
	}
#ifndef WIN32
	if(buf+len+sizeof(uint16_t) > _end) {
		yobotproto_log_err("len is %d but only have %lu for buffer",len,
				_end-(buf+sizeof(uint16_t)+len));
		goto err;
	}
#endif

	ret.data = malloc(len);
	memcpy(ret.data,buf+2,len);
	ret.len = len;
	return ret;

	err:
	yobotproto_log_warn("returning empty segment_r");
	ret.len = 0;
	if(ret.data) free(ret.data);
	ret.data = NULL;
	return ret;
}

struct segment_r yobot_proto_read_segment(void *input) {
#define full_read(size) \
	nread = 0; \
	while (nread < size) { \
		/*err = read(fd,bufp,size-nread);*/ \
		err = recv(fd,bufp,size-nread,0); \
		if (err <= 0) { \
			if ((errno == EWOULDBLOCK) && err != 0) { \
				yobotproto_log_debug("continuing to read...");\
				usleep(100); \
				continue; \
			} else /*got a HUP*/ { \
				ret.read_return = err; \
				free(buf); \
				return ret; \
			} \
		} \
		nread += err; \
		bufp += nread; \
	}
	struct segment_r ret;
	ret.data = NULL;
	ret.len = 0;

	int fd = *(int*)input;
	int status;
	YOBOT_SET_SOCK_BLOCK(fd, 1, status);
	//fcntl(fd,F_SETFL,fcntl(fd,F_GETFL)|O_NONBLOCK);

	uint16_t len=0, nread=0, err=0;
	char *buf = malloc(YOBOT_MAX_COMMSIZE);
	char *bufp = buf;
	/*read a short*/
	full_read(2);

	bufp -= 2;
	len = ntohs(*(uint16_t*)bufp);

	if (len > YOBOT_MAX_COMMSIZE) {
		yobotproto_log_err("LEGNTH %d EXCEEDS MAX %d!\n",
				len, YOBOT_MAX_COMMSIZE);
		free(buf);
		return ret;
	}
	/*read the rest*/
	full_read(len);

	ret.len = len;
	ret.data = buf;

	return ret;
#undef full_read
}

void yobot_protoclient_init(ssize_t (*data_function)(int,void*,size_t)) {
	yobot_proto_get_segment = yobot_proto_read_segment;
}

void *yobot_protoclient_comm_encode(yobotcomm *comm, const char *data,
		uint32_t len, void *output, yobot_protoclient_output out_type) {
	yobot_proto_model_internal model;
	model.comm = comm;
	if (len) {
		model.commdata_u.simple_comm_data = data;
		model.comm->len = len;
	} else {
		model.commdata_u.simple_comm_data = NULL;
		comm->len = 0;
	}
	return yobot_proto_segment_encode(&model,output,out_type);
}

void *yobot_protoclient_cmd_encode(struct yobot_cmdinfo cmdinfo,
		void *output, yobot_protoclient_output out_type) {
	yobot_proto_model_internal model;
	yobotcomm _comm;
	yobotcomm *comm = &_comm; /*nasty hack*/
	yobotcmd *cmd = malloc(sizeof(yobotcmd));
	memset(cmd, 0, sizeof(yobotcmd));
	memset(comm, 0, sizeof(comm));
	size_t len = cmdinfo.len;
	const void *data = cmdinfo.data;

	comm->flags = cmdinfo.commflags;
	comm->reference = cmdinfo.reference;
	cmd->acct_id = cmdinfo.acctid;
	cmd->command = cmdinfo.command;
	cmd->len = cmdinfo.len;

	model.comm = comm;
	model.commtype_u.cmd_s.cmd = cmd;
	comm->type = YOBOT_COMMTYPE_CMD;
//	printf("%s: COMMAND %d\n", __func__, cmd->command);
	if (len) {
		model.commdata_u.cmddata_u.simple_cmd_payload = data;
		model.commtype_u.cmd_s.type.simple_cmdpayload = data;
		cmd->len = len;
	} else {
		model.commdata_u.cmddata_u.simple_cmd_payload = NULL;
		model.commtype_u.cmd_s.type.simple_cmdpayload = NULL;
		cmd->len = 0;
	}
	comm->len = 0;
	return yobot_proto_segment_encode(&model,output,out_type);
	g_free(cmd);
}

void *yobot_protoclient_mkacct_encode(struct yobot_mkacctinfo info,
		void *output, yobot_protoclient_output out_type) {

	yobot_proto_model_internal model;
	yobotcomm comm;
	yobotcmd cmd;
	yobotmkacct acctrq;
	yobotmkacct_internal arq_data;

	uint32_t id = info.acctid;
	const char *user = info.user;
	const char *passw = info.password;
	yobot_proto_improto proto = info.improto;

	comm.type = YOBOT_COMMTYPE_CMD;
	comm.len = 0;
	comm.flags = info.commflags;
	comm.reference = info.reference;

	cmd.command = YOBOT_CMD_ACCT_NEW;
	cmd.acct_id = acctrq.id = id;
	cmd.len = 0;

	acctrq.namelen = (int)strlen(user) + 1;
	acctrq.passlen = (int)strlen(passw) + 1;
	acctrq.improto = proto;
	acctrq.id = id;

	arq_data.pass = passw;
	arq_data.user = user;

	model.commdata_u.cmddata_u.acctreqpayload = &arq_data;
	model.comm = &comm;
	model.commtype_u.cmd_s.cmd = &cmd;
	model.commtype_u.cmd_s.type.accreq = &acctrq;
	return yobot_proto_segment_encode(&model, output, out_type);
}

void *yobot_protoclient_msg_encode(struct yobot_msginfo info,
		void *output, yobot_protoclient_output out_type)
{
	const char *who = info.who;
	const char *to = info.to;
	const char *msg = info.txt;
	uint32_t acct_id = info.acctid;
	yobot_proto_flags flags = info.commflags;
	PurpleMessageFlags prpl_flags = info.purple_flags;
	uint32_t mtime = info.msgtime;

//	printf("%s: got WHO as %s\n", __func__, who);
	yobot_proto_model_internal model;
	yobotmsg ymsg;
	yobotcmd cmd;
	yobotcomm comm;
	yobotmsg_internal mdata;
	mdata.to = to;
	mdata.txt = msg;
	mdata.who = who;

	ymsg.data_len = ((mdata.txt != NULL) && strlen(mdata.txt) >= 1) ?
			strlen(mdata.txt) +1 : 0;
	ymsg.who_len = ((mdata.who != NULL) && strlen(mdata.who) >= 1) ?
			strlen(mdata.who) +1 : 0;
	ymsg.to_len = strlen(to) + 1;

	ymsg.msgtime = (uint32_t)mtime;
	ymsg.msgflags = prpl_flags;

	comm.flags = flags;
	comm.type = YOBOT_COMMTYPE_CMD;
	comm.len = 0;
	comm.reference = info.reference;

	cmd.command = YOBOT_CMD_MSG_SEND;
	cmd.acct_id = acct_id;
	cmd.len = 0;

	model.comm = &comm;
	model.commtype_u.cmd_s.cmd = &cmd;
	model.commtype_u.cmd_s.type.msg = &ymsg;
	model.commdata_u.cmddata_u.msgpayload = &mdata;
//	puts("done");

	return yobot_proto_segment_encode(&model,output,out_type);
}
//yobot_proto_event yev,
//		yobot_proto_purple_type purple_type, yobot_proto_evtype evtype,
//		int obj_id, int len, const char *data
void *yobot_protoclient_event_encode(struct yobot_eventinfo info, void *output,
		yobot_protoclient_output out_type)
{
	yobot_proto_event yev = info.event;
	yobot_proto_purple_type purple_type = info.purple_type;
	if (info.purple_type) {
		purple_type = purple_type;
	} else {
		purple_type = YOBOT_PURPLE_ACCOUNT;
	}
	yobot_proto_evtype evtype;
	if (info.severity) {
		evtype = info.severity;
	} else {
		evtype = YOBOT_INFO;
	}
	uint32_t obj_id = info.acctid;
	size_t len = info.len;
	const char *data = info.data;

//	puts(__func__);
	yobot_proto_model_internal model;
	yobotcomm comm;
	yobotevent evt;

	comm.len = 0;
	comm.type = YOBOT_COMMTYPE_EVENT;
	comm.flags = info.commflags;
	comm.reference = info.reference;

	evt.event = yev;
	evt.len = len;
	evt.event_type = evtype;
	evt.obj_id = obj_id;
	evt.purple_type = purple_type;

	model.comm = &comm;
	model.commtype_u.evt = &evt;
	model.commdata_u.simple_comm_data = data;

	return yobot_proto_segment_encode(&model, output, out_type);
}

static void pack_valstruct_in_buf(char *tplstring, size_t typsz,
		const void *data, char **bufp, uint16_t *bufsz)
{
#ifdef USE_TPL
	size_t tplsz;
	char *tplbuf;
	tpl_node *tn = tpl_map(tplstring,data);
	tpl_pack(tn, 0);
	tpl_dump(tn, TPL_MEM, &tplbuf, &tplsz);
	memcpy(*bufp, tplbuf, tplsz);
	*bufp += tplsz;
	*bufsz += tplsz;
	tpl_free(tn);
	free(tplbuf);
#else
	memcpy(bufp, data, typsz);
	*bufp += typsz;
	*bufsz += typsz;
#endif
}

void *yobot_proto_segment_encode(yobot_proto_model_internal *model, void *output,
		yobot_protoclient_output out_type)
{
#ifndef WIN32
	tpl_hook.oops = printf;
#endif
	uint16_t bufsz = 0;

	char buf[YOBOT_MAX_COMMSIZE];
	memset(buf,0,YOBOT_MAX_COMMSIZE);

	char *bufp = buf + 2; /*for the length*/
	const char *simple_data = NULL;
	yobotcomm *comm = model->comm;

	pack_valstruct_in_buf(yobot_proto_tpl_comm,sizeof(yobotcomm),comm,
			&bufp,&bufsz);

	if (comm->type == YOBOT_COMMTYPE_EVENT) {
		yobotevent *evt = model->commtype_u.evt;
		if ((simple_data = model->commdata_u.simple_comm_data))
			assert(evt->len > 0);
		else
			evt->len = 0;
		pack_valstruct_in_buf(yobot_proto_tpl_event, sizeof(yobotevent), evt,
				&bufp, &bufsz);
		bufsz += evt->len;
		if(evt->len)
			memcpy(bufp,simple_data,evt->len);
	}
	else if(comm->type == YOBOT_COMMTYPE_CMD)
	{
		yobotcmd *cmd = model->commtype_u.cmd_s.cmd;
		pack_valstruct_in_buf(yobot_proto_tpl_cmd, sizeof(yobotcmd), cmd,
				&bufp, &bufsz);

		if (cmd->command == YOBOT_CMD_MSG_SEND) {
			yobotmsg *msg = model->commtype_u.cmd_s.type.msg;
			const char *to = model->commdata_u.cmddata_u.msgpayload->to;
			const char *txt = model->commdata_u.cmddata_u.msgpayload->txt;
			const char *who = model->commdata_u.cmddata_u.msgpayload->who;

			assert(to);

			msg->data_len = (txt && strlen(txt) >= 1) ? (strlen(txt) + 1) : 0;
			msg->who_len = (who && strlen(who) >= 1) ? (strlen(who) + 1) : 0;
			msg->to_len = strlen(to) + 1;
			pack_valstruct_in_buf(yobot_proto_tpl_msg, sizeof(yobotmsg),msg,
					&bufp, &bufsz);

			memcpy(bufp,to,msg->to_len);
			bufp += msg->to_len;

			if (txt) memcpy(bufp,txt,msg->data_len);
			bufp += msg->data_len;

			if (who) {
				memcpy(bufp,who,msg->who_len);
				bufp += msg->who_len;
			}

			bufsz += (msg->data_len + msg->to_len + msg->who_len);
			assert(bufsz < YOBOT_MAX_COMMSIZE);

		}
		else if (cmd->command == YOBOT_CMD_ACCT_NEW) {
			yobotproto_log_info("new account");
			yobotmkacct *acct_req = model->commtype_u.cmd_s.type.accreq;
			const char *user = model->commdata_u.cmddata_u.acctreqpayload->user;
			const char *pass = model->commdata_u.cmddata_u.acctreqpayload->pass;
			assert(user); assert(pass);
			acct_req->namelen = strlen(user) + 1;
			acct_req->passlen = strlen(pass) + 1;
			bufsz += (acct_req->namelen + acct_req->passlen);
			assert(bufsz < YOBOT_MAX_COMMSIZE);
			yobotproto_log_debug("USER:%s PASS:%s \n", user, pass);

			pack_valstruct_in_buf(yobot_proto_tpl_mkacct, sizeof(yobotmkacct),
					acct_req, &bufp, &bufsz);
			memcpy(bufp,user,acct_req->namelen);
			bufp += acct_req->namelen;
			memcpy(bufp, pass, acct_req->passlen);
			bufp += acct_req->passlen;
		}
		else if((simple_data = model->commtype_u.cmd_s.type.simple_cmdpayload) != NULL) {
			cmd->len = strlen(simple_data) + 1;
			bufsz += cmd->len;
			assert(bufsz < YOBOT_MAX_COMMSIZE);
			memcpy(bufp,simple_data,cmd->len);
			bufp += cmd->len;
		}
	}

	/*Now write the actual message to the fd/buffer*/
//	printf("bufsz is %d\n",bufsz);
	*(uint16_t*)buf = htons(bufsz);
//	printf("%s: BUFSZ=%d\n", __func__, bufsz);
	if (out_type == YOBOT_PROTOCLIENT_TO_FD) {
		/*block....*/
		int fd = *(int*) output;
		int status;
		YOBOT_SET_SOCK_BLOCK(fd, 0, status)
		if(send(fd,buf,bufsz+2,0) == -1) {
			perror(__func__);
		}
		YOBOT_SET_SOCK_BLOCK(fd, 1, status);
		/*done...*/
	} else if (out_type == YOBOT_PROTOCLIENT_TO_BUF) {
		void *retbuf = malloc(bufsz+2);
		memcpy(retbuf, buf, bufsz+2);
		return retbuf;
	}
	return NULL;
}

/*some funky macros*/
#ifndef USE_TPL
#define funky_macro_get_valstruct(stype, fd, sptr) \
	if(!(read_data(fd,sptr,sizeof(yobot##stype)))) goto err;
#else
#define funky_macro_get_valstruct(stype,sptr) \
	size_t _tplsz; \
	tpl_node *tn = tpl_map(yobot_proto_tpl_##stype,sptr); \
	if(tpl_load(tn, TPL_MEM|TPL_EXCESS_OK,seginfo->data,seginfo->len)<0) goto err; \
	if(tpl_unpack(tn,0)<=0) goto err; \
	tpl_node *_tn2 = tpl_map(yobot_proto_tpl_##stype,sptr); \
	tpl_pack(_tn2,0); \
	tpl_dump(_tn2,TPL_GETSIZE,&_tplsz); \
	tpl_free(_tn2); \
	\
	seginfo->data += _tplsz; \
	seginfo->len -= _tplsz; \
	if (seginfo->len < 0) goto err; \
	tpl_free(tn);\
	tn = NULL;
#endif


#ifdef USE_TPL
#define funky_macro_errhandler(stype) \
	yobotproto_log_crit("BAILING!"); \
	tpl_free(tn); \
	free_yobot##stype##_internal(ret); \
	return 0;
#else
#define funky_macro_errhandler(stype) \
	yobotproto_log_crit("BAILING!"); \
	yobot_proto_free_yobot##stype##_internal(ret); \
	return 0;
#endif

#define funky_macro_copy_and_advance_buf(target,explen) \
	if(explen > 0) { \
		if (explen > seginfo->len) goto err; \
		target = malloc(explen); \
		memcpy((void*)target,seginfo->data,explen); \
		seginfo->data += explen; \
		seginfo->len -= explen; \
		}

static yobotmsg_internal *msg_decode(struct segment_r *seginfo)
{
	yobotmsg_internal *ret = malloc(sizeof(yobotmsg_internal));
	ret->yomsg = malloc(sizeof(yobotmsg));
	ret->to = NULL;
	ret->txt = NULL;
	ret->who = NULL;

	funky_macro_get_valstruct(msg,ret->yomsg);
	assert((ret->yomsg->to_len + ret->yomsg->data_len + ret->yomsg->who_len )
			< YOBOT_MAX_COMMSIZE); /*sanity check*/

	if(!ret->yomsg->to_len) goto err;

	funky_macro_copy_and_advance_buf(ret->to,ret->yomsg->to_len);
	funky_macro_copy_and_advance_buf(ret->txt,ret->yomsg->data_len);
	funky_macro_copy_and_advance_buf(ret->who,ret->yomsg->who_len);

	return ret;

	err:
	funky_macro_errhandler(msg)

}
static yobotmkacct_internal *mkacct_decode(struct segment_r *seginfo)
{
	yobotmkacct_internal *ret = malloc(sizeof(yobotmkacct_internal));
	ret->yomkacct = malloc(sizeof(yobotmkacct));
	ret->user = NULL;
	ret->pass = NULL;

	funky_macro_get_valstruct(mkacct,ret->yomkacct);

	funky_macro_copy_and_advance_buf(ret->user,ret->yomkacct->namelen);
	funky_macro_copy_and_advance_buf(ret->pass,ret->yomkacct->passlen);

	return ret;

	err:
	funky_macro_errhandler(mkacct)
}

static yobotevent_internal *event_decode(struct segment_r *seginfo)
{
	yobotevent_internal *ret = malloc(sizeof(yobotevent_internal));
	ret->evt = malloc(sizeof(yobotevent));
	ret->data = NULL;
	funky_macro_get_valstruct(event,ret->evt);

	funky_macro_copy_and_advance_buf(ret->data,ret->evt->len);

	return ret;

	err:
	funky_macro_errhandler(event)
}

/*This is mainly for python where the read calls might be more expensive for it*/
static void *comm_decode(struct segment_r *seginfo, yobotcomm *comm) {
	funky_macro_get_valstruct(comm,comm);
	return comm;
	/*we need an internal structure with a variable length pointer here...*/
	err:
#ifdef USE_TPL
	tpl_free(tn);
#endif
	return NULL;
}

static yobotcmd_internal *cmd_decode(struct segment_r *seginfo) {

	yobotcmd_internal *ret = malloc(sizeof(yobotcmd_internal));
	ret->cmd = malloc(sizeof(yobotcmd));
	ret->data = NULL;
	ret->type.simple_cmdpayload = ret->data;

	funky_macro_get_valstruct(cmd,ret->cmd);
	funky_macro_copy_and_advance_buf(ret->data,ret->cmd->len);

	ret->type.simple_cmdpayload = ret->data;

	return ret;

	err:
	funky_macro_errhandler(cmd)
}

/*this function is because swig demands all C buffers it receives are to be
 * malloc'd, and swig demands that it be able to free() them. Here we will
 * try to hide this from swig by simply returning a yobot_protoclient_segment
 * without doing anything else
 */

yobot_protoclient_segment *yobot_protoclient_segment_decode_from_buf(
		char *buf, int len) {
	//FIXME: this should be merged with segfrombuf.. eventually..
	struct segment_r seginfo;
	seginfo.data = malloc(len); /*free()d by segment_decode()*/
	seginfo.len = len;
	memcpy(seginfo.data, buf, len); /*since we will free this,
	we can't use our original buffer*/
	return yobot_protoclient_segment_decode(seginfo);

}

yobot_protoclient_segment *yobot_protoclient_segment_decode(
		struct segment_r seginfo) {

	if((!(seginfo.data))||(!(seginfo.len))) return NULL;

	void *bufstart = seginfo.data;

	yobot_protoclient_segment *seg = malloc(sizeof(yobot_protoclient_segment));
	memset(seg,0x0,sizeof(yobot_protoclient_segment));
	yobotcomm *comm = malloc(sizeof(yobotcomm));
	seg->comm = comm;

	if(!(comm_decode(&seginfo,comm))) goto err;

	if (comm->type == YOBOT_COMMTYPE_CMD) {
		seg->cmdi = cmd_decode(&seginfo);
		if(!seg->cmdi) goto err;

		if(seg->cmdi->cmd->command == YOBOT_CMD_ACCT_NEW)  {
			seg->mkaccti = mkacct_decode(&seginfo);
			if(!seg->mkaccti) goto err;
			seg->struct_type = YOBOT_PROTOCLIENT_YMKACCTI;
		}

		else if(seg->cmdi->cmd->command == YOBOT_CMD_MSG_SEND) {
			seg->msgi = msg_decode(&seginfo);
			if(!seg->msgi) goto err;
			seg->struct_type = YOBOT_PROTOCLIENT_YMSGI;
		}

		else {
			seg->struct_type = YOBOT_PROTOCLIENT_YCMDI;
		}
	}
	else if(comm->type == YOBOT_COMMTYPE_EVENT) {
		seg->struct_type = YOBOT_PROTOCLIENT_YEVTI;
		seg->evi = event_decode(&seginfo);
		seg->rawdata = seg->evi->data;
		if(!seg->evi) goto err;
	}
	else {
		goto err;
	}

	free(bufstart);
	seginfo.data = NULL;
	return seg;

	err:
	seginfo.data = NULL;
	free(bufstart);
	yobot_protoclient_free_segment(seg);
	return NULL;
}
void yobot_protoclient_free_segment(yobot_protoclient_segment *seg) {
	if(!seg) return;
	if(seg->comm) free(seg->comm);
	if(seg->cmdi) free_yobotcmd_internal(seg->cmdi);
	if(seg->msgi) free_yobotmsg_internal(seg->msgi);
	if(seg->evi) free_yobotevent_internal(seg->evi);
	if(seg->mkaccti) free_yobotmkacct_internal(seg->mkaccti);
	free(seg);
}
static void free_yobotmkacct_internal(yobotmkacct_internal *ymkaccti) {
	free(ymkaccti->yomkacct);
	free((void*)ymkaccti->user);
	free((void*)ymkaccti->pass);
	free(ymkaccti);
}

static void free_yobotcmd_internal(yobotcmd_internal *yci) {
	free((void*)yci->data);
	free(yci->cmd);
	free(yci);
}

static void free_yobotevent_internal(yobotevent_internal *p) {
	free((void*)p->data);
	free(p->evt);
	free(p);
}

static void free_yobotmsg_internal(yobotmsg_internal *p) {
	free((void*)p->to);
	free((void*)p->txt);
	free((void*)p->who);
	free(p->yomsg);
	free(p);
}
