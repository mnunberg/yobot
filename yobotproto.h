/*yobotproto.h*/

#ifndef YOBOTPROTO_H_
#define YOBOTPROTO_H_

#ifndef SWIG
#include <stdint.h>
#include <purple.h>
#endif

//#define YOBOT_MAX_COMMSIZE 0x0fffff /*1MB*/
#define YOBOT_MAX_COMMSIZE (1<<16)-1
#define YOBOT_USER_SELF "*"
#define YOBOT_TEXT_DELIM "\x01"

/*These will typically be sent from the python client to the C server*/
typedef enum {
	YOBOT_CMD_ROOM_JOIN = 1,
	YOBOT_CMD_ROOM_LEAVE,
	YOBOT_CMD_ROOM_GET,

	YOBOT_CMD_MSG_SEND,

	YOBOT_CMD_USER_UNIGNORE,
	YOBOT_CMD_USER_IGNORE,
	YOBOT_CMD_USER_ADD,
	YOBOT_CMD_USER_REMOVE,
	YOBOT_CMD_USER_AUTHORIZE_ADD_ACCEPT,
	YOBOT_CMD_USER_AUTHORIZE_ADD_DENY,

	YOBOT_CMD_CONNECT,
	YOBOT_CMD_SHUTDOWN,

	YOBOT_CMD_ACCT_ENABLE,
	YOBOT_CMD_ACCT_DISABLE,
	YOBOT_CMD_ACCT_REMOVE,
	YOBOT_CMD_ACCT_NEW,
	YOBOT_CMD_ACCT_ID_REQUEST,

	YOBOT_CMD_STATUS_CHANGE,

	YOBOT_CMD_CLIENT_REGISTER,
	YOBOT_CMD_CLIENT_RMACCT,

	YOBOT_CMD_ROOM_FETCH_USERS,
	YOBOT_CMD_FETCH_BUDDIES,
	YOBOT_CMD_FETCH_BUDDY_ICONS,

	YOBOT_CMD_REQUEST_BACKLOG,
	YOBOT_CMD_PURPLE_REQUEST_GENERIC_RESPONSE,

	YOBOT_CMD_FETCH_OFFLINE_MSGS,
} yobot_proto_cmd;

typedef enum {
	YOBOT_PURPLE_ACCOUNT = 100,
	YOBOT_PURPLE_CONV,
	YOBOT_PURPLE_CORE
} yobot_proto_purple_type;

/*Sent from the C server to the python client*/
typedef enum {
	/*Connections*/
	YOBOT_EVENT_DUMMY = 1,
	YOBOT_EVENT_CONNECTED = 2,
	YOBOT_EVENT_CONNECTING,
	YOBOT_EVENT_DISCONNECTED,

	YOBOT_EVENT_NOTICE,

	/*Account events*/
	YOBOT_EVENT_ACCT_REGISTERED,
	YOBOT_EVENT_ACCT_UNREGISTERED,
	YOBOT_EVENT_ACCT_REMOVED,
	YOBOT_EVENT_ACCT_ID_CHANGE,
	YOBOT_EVENT_ACCT_ID_NEW,

	/*Login events*/
	YOBOT_EVENT_AUTH_FAIL,
	YOBOT_EVENT_LOGIN_ERR,
	YOBOT_EVENT_LOGIN_TIMEOUT,

	/*Room Events*/
	YOBOT_EVENT_ROOM_JOINED,
	YOBOT_EVENT_ROOM_JOINING,
	YOBOT_EVENT_ROOM_JOIN_FAILED,
	YOBOT_EVENT_ROOM_LEFT,
	YOBOT_EVENT_ROOM_USER_JOIN,
	YOBOT_EVENT_ROOM_USER_LEFT,
	YOBOT_EVENT_ROOM_TOPIC_CHANGED,

	YOBOT_EVENT_USER_ADDREQ,
	YOBOT_EVENT_STATUS_CHANGE,

	YOBOT_EVENT_ERR,

	/*Client events*/
	YOBOT_EVENT_CLIENT_REGISTERED,
	YOBOT_EVENT_CLIENT_REGISTER_ID_UNAVAILABLE,
	YOBOT_EVENT_CLIENT_ERR_BADREQUEST,

	/*Buddy status events*/
	YOBOT_EVENT_BUDDY_ONLINE,
	YOBOT_EVENT_BUDDY_OFFLINE,
	YOBOT_EVENT_BUDDY_INVISIBLE,
	YOBOT_EVENT_BUDDY_BUSY,
	YOBOT_EVENT_BUDDY_IDLE,
	YOBOT_EVENT_BUDDY_UNIDLE,
	YOBOT_EVENT_BUDDY_AWAY,
	YOBOT_EVENT_BUDDY_BRB,

	YOBOT_EVENT_BUDDY_GOT_ICON,
	/*fetch request responses*/
	YOBOT_EVENT_ROOM_FETCH_USER_RESPONSE,
	YOBOT_EVENT_ROOM_FETCH_USER_RESPONSE_END,
	YOBOT_EVENT_BUDDY_FETCH_RESPONSE,
	YOBOT_EVENT_BUDDY_FETCH_RESPONSE_END,

	/*notifications and client requests*/
	YOBOT_EVENT_PURPLE_REQUEST_GENERIC,
	YOBOT_EVENT_PURPLE_REQUEST_GENERIC_CLOSED,
	YOBOT_EVENT_PURPLE_NOTICE_GENERIC,
	YOBOT_EVENT_AGENT_NOTICE_GENERIC,

} yobot_proto_event;

typedef enum {
	YOBOT_INFO = 1,
	YOBOT_WARN,
	YOBOT_ERR,
	YOBOT_CRIT,
	YOBOT_PURPLE_CONNECTION_ERROR,
	YOBOT_CLIENT_INTERNAL,
	YOBOT_CLIENT_ERROR,
} yobot_proto_evtype;

typedef enum {
	YOBOT_COMMTYPE_CMD,
	YOBOT_COMMTYPE_EVENT,
	YOBOT_COMMTYPE_RESULT,
	YOBOT_COMMTYPE_STREAM,
} yobot_proto_commtype;

/*these can be OR'd*/

typedef enum {
	YOBOT_SUCCESS = 		1 << 0,
	YOBOT_ERR_ENOTINROOM = 	1 << 1,
	YOBOT_ERR_ENOTCONNECTED=1 << 2,
	YOBOT_ERR_ENOSUCHUSER = 1 << 3,
	YOBOT_ERR_INTERNAL = 	1 << 4,
} yobot_proto_errors;

typedef enum {
	/*Message types*/
	YOBOT_MSG_TYPE_CHAT = 	1 << 0,
	YOBOT_MSG_TYPE_IM = 	1 << 1,
	YOBOT_MSG_ATTENTION = 	1 << 2,
	/*Message direction*/
	YOBOT_MSG_TO_SERVER = 	1 << 3,
	/*request/response*/
	YOBOT_RESPONSE = 		1 << 4,
	YOBOT_RESPONSE_END  = 	1 << 5,
	YOBOT_BACKLOG = 		1 << 6,
	YOBOT_DATA_IS_BINARY = 	1 << 7,
	YOBOT_OFFLINE_MSG = 	1 << 8,

} yobot_proto_flags;

typedef enum {
	YOBOT_YAHOO = 1,
	YOBOT_AIM,
	YOBOT_IRC,
	YOBOT_MSN,
	YOBOT_GTALK,
	YOBOT_JABBER,
} yobot_proto_improto;


typedef enum {
	YOBOT_REQUEST_OK = 4096,
	YOBOT_REQUEST_CANCEL,
	YOBOT_REQUEST_INPUT,
} yobot_proto_request_cb;

typedef enum {
	YOBOT_ACTIONTYPE_OK,
	YOBOT_ACTIONTYPE_CANCEL
} yobot_proto_actiontype;
/*Typedefs*/
#define _TPL_ENUM_T "i"

typedef int32_t ycommlen_t;
#define _TPL_COMMLEN_T "i"
typedef uint8_t ybcommref_t;
#define _TPL_COMMREF_T "c"
typedef uint8_t ybmsgtolen_t;
#define _TPL_MSGTOLEN_T "c"
typedef uint16_t ybmsgdatalen_t;
#define _TPL_MSGDATALEN_T "v"
typedef uint8_t ybmsgwholen_t;
#define _TPL_MSGWHOLEN_T "c"
typedef uint32_t ybtime_t;
#define _TPL_YBTIME_T "u"
typedef uint32_t ybacctid_t;
#define _TPL_YBACCTID_T "u"
typedef uint16_t ybevtlen_t;
#define _TPL_EVTLEN_T "u"
typedef uint16_t ybcmdlen_t;
#define _TPL_CMDLEN_T "v"
typedef uint8_t ybnamelen_t;
#define _TPL_YBNAMELEN_T "c"
typedef uint8_t ybpasslen_t;
#define _TPL_YBPASSLEN_T "c"
typedef uint16_t ybparamlen_t;
#define _TPL_YBPARAMLEN_T "v"

/*all communication uses this struct*/
/*uint16_t segment_len*/
typedef struct {
	ycommlen_t len;
	yobot_proto_commtype type;
	yobot_proto_flags flags;
	ybcommref_t reference;
/*	char *data; */
} yobotcomm;
#define yobot_proto_tpl_comm_layout _TPL_COMMLEN_T _TPL_ENUM_T \
	_TPL_ENUM_T _TPL_COMMREF_T
//"iiiv"
#define yobot_proto_tpl_comm "S(" yobot_proto_tpl_comm_layout ")"

/*chat message, sent to a user or a room*/
typedef struct {
	ybmsgtolen_t to_len;
	ybmsgdatalen_t data_len;
	ybmsgwholen_t who_len;
	ybtime_t msgtime;
	PurpleMessageFlags msgflags;
/*	char *to;*/
/*	char *data;*/
/*  char *who*/
} yobotmsg;
#define yobot_proto_tpl_msg_layout _TPL_MSGTOLEN_T _TPL_MSGDATALEN_T \
	_TPL_MSGWHOLEN_T _TPL_YBTIME_T _TPL_ENUM_T
//"cvcvui"
#define yobot_proto_tpl_msg "S(" yobot_proto_tpl_msg_layout ")"

typedef struct {
	yobot_proto_cmd command;
	ybacctid_t acct_id;
	ybcmdlen_t len;
} yobotcmd;
#define yobot_proto_tpl_cmd_layout _TPL_ENUM_T _TPL_YBACCTID_T _TPL_CMDLEN_T
//"iuv"
#define yobot_proto_tpl_cmd "S(" yobot_proto_tpl_cmd_layout ")"

typedef struct {
	yobot_proto_improto improto;
	ybacctid_t id;
	ybnamelen_t namelen;
	ybpasslen_t passlen;
	ybparamlen_t paramlen;
} yobotmkacct;
#define yobot_proto_tpl_mkacct_layout _TPL_ENUM_T _TPL_YBACCTID_T _TPL_YBNAMELEN_T _TPL_YBPASSLEN_T _TPL_YBPARAMLEN_T
//"iucc"
#define yobot_proto_tpl_mkacct "S(" yobot_proto_tpl_mkacct_layout ")"

typedef struct {
	yobot_proto_event event;
	yobot_proto_purple_type purple_type;
	yobot_proto_evtype event_type;
	ybacctid_t obj_id;
	ybevtlen_t len;
	/*char *data*/
} yobotevent;
#define yobot_proto_tpl_event_layout _TPL_ENUM_T _TPL_ENUM_T _TPL_ENUM_T _TPL_YBACCTID_T _TPL_EVTLEN_T
//"iiiuv"
#define yobot_proto_tpl_event "S(" yobot_proto_tpl_event_layout ")"
/*END YOBOT PROTOCOL*/

/*This represents the logical structure of the protocol
 * since it only contains pointers it is designed exclusively
 * for internal use, to make things more readable*/
typedef struct {
	yobotmsg *yomsg; /*pointer to a fixed-length yobotmsg object*/
	const char *to;
	const char *txt;
	const char *who;
} yobotmsg_internal;
#define yobot_proto_tpl_msgi "S($("\
		yobot_proto_tpl_msg_layout ")"\
		"sss)"

typedef struct {
	yobotmkacct *yomkacct;
	const	char *user;
	const char *pass;
	const char *attr_xml;
} yobotmkacct_internal;
#define yobot_proto_tpl_mkaccti "S($(" \
		yobot_proto_tpl_mkacct_layout ")" \
		"ss)"

typedef struct {
	yobotevent *evt;
	const char *data;
} yobotevent_internal;
#define yobot_proto_tpl_eventi "S($(" \
		yobot_proto_tpl_event_layout ")" \
		"s)"

typedef union { /*complex types e.g. structs*/
	yobotmsg_internal *msgpayload;
	yobotmkacct_internal *acctreqpayload;
	const void *simple_cmd_payload;
} _cmd_data_u;

typedef union  {
	const void *simple_cmdpayload; /*simple primitive types*/
	yobotmsg *msg;
	yobotmkacct *accreq;
} _cmd_type_u;


typedef struct {
	yobotcmd *cmd;
	_cmd_type_u type;
	char *data;
} yobotcmd_internal;
//TODO: Remove union and adapt to TPL

typedef union  {
	yobotcmd_internal cmd_s; /*commands*/
	yobotevent *evt; /*event*/
} _comm_type_u;

typedef union {
	const void *simple_comm_data;
	_cmd_data_u cmddata_u;
} _comm_data_u;

/*simple protocol structure*/

typedef struct {
	yobotcomm *comm; /*our base object*/
	_comm_type_u commtype_u;
	_comm_data_u commdata_u;
} yobot_proto_model_internal;


#ifndef SWIG

#define yobot_proto_get_modelmsg(modelp) \
	modelp->commtype_u.cmdtype_u.msg
#define yobot_proto_get_modelmsgi(modelp) \
	modelp->commdata_u.cmddata_u.msgpayload

#define yobot_proto_get_prpl_id(I) \
	(I == YOBOT_YAHOO ? "prpl-yahoo" : \
	(I == YOBOT_IRC ? "prpl-irc" :\
	(I == YOBOT_AIM ? "prpl-aim" : \
	(I == YOBOT_MSN ? "prpl-msn" : \
	(I == YOBOT_GTALK ? "prpl-jabber" : \
	(I == YOBOT_JABBER ? "prpl-jabber" : \
			NULL))))))

#define yobot_proto_get_conv_type(yobot_flag) \
	(YOBOT_MSG_TYPE_CHAT & yobot_flag) ? PURPLE_CONV_TYPE_CHAT : PURPLE_CONV_TYPE_IM


#endif /*SWIG*/

#endif /* YOBOTPROTO_H_ */
