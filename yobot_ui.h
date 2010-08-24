#include <purple.h>
#include <glib.h>
#include "yobotproto.h"
#ifndef HAVE_CHATROOM_H_
#define HAVE_CHAROOM_H_

#ifdef WIN32
#define _WIN32_WINNT 0x0501
	#include <winsock2.h>
	#include <ws2tcpip.h>
	#define EWOULDBLOCK WSAEWOULDBLOCK
#else
	#include <sys/socket.h>
	#include <netinet/in.h>
	#include <netdb.h>
	typedef struct sockaddr_storage xsockaddr_storage;
#endif


/*a macro*/
#define yobot_get_acct_id(acct)  acct->ui_data ? ((account_uidata*)acct->ui_data)->id : 0

#define YOBOT_LISTEN_COND (PURPLE_INPUT_WRITE << 1)
#define YOBOT_HUP_COND (YOBOT_LISTEN_COND << 1)

typedef struct {
	PurpleAccountRequestAuthorizationCb deny_cb;
	PurpleAccountRequestAuthorizationCb allow_cb;
	void *user_data;
} authrequest;

typedef struct {
	uint32_t id;
	GHashTable *requests;
} account_uidata;

void yobot_core_ui_init(void);

/*To be filled in by the actual modules*/
extern void yobot_conversation_signals_register(void); /*yobot_conversation.c.. i think*/
extern void yobot_connection_signals_register(void); /*yobot_uiops.c*/
extern void yobot_account_signals_register(void); /*yobot_uiops.c*/
extern void yobot_blist_signals_register(void); /*yobot_uiops.c*/

extern void yobot_user_authorize(PurpleAccount *account, const char *user, gboolean accept);

extern PurpleConnectionUiOps yobot_connection_uiops; /*yobot_uiops.c*/
extern PurpleConversationUiOps yobot_conversation_uiops; /*yobot_conversation.c*/
extern PurpleAccountUiOps yobot_account_uiops;
extern PurpleBlistUiOps yobot_blist_uiops; /*yobot_blist.c*/

/*implemented in yobot_ui.c*/
extern int client_write_fd;
extern int server_write_fd;
extern GHashTable *yobot_acct_table;
extern GHashTable *yobot_request_table;

/*Signal Handlers*/
void chatroom_got_chat_post(PurpleAccount*, char *sender,
		char *message, PurpleConversation *conv, PurpleMessageFlags);
void *chatroom_chat_joined(PurpleConversation *conv);
void *chatroom_chat_join_failed(PurpleConnection *gc, GHashTable *components);
void chatroom_sending_chat_msg(PurpleAccount *account, char **message, int id);
void chatroom_sent_chat_msg(PurpleAccount *gc, const char *message, int id);
void chatroom_chat_left(PurpleConversation *conv);

/*UiOps*/
void chatroom_create_conversation(PurpleConversation *conv);
void chatroom_write_chat(PurpleConversation *conv, const char *who,
		const char *message, PurpleMessageFlags flags, time_t mtime);
void chatroom_write_conv(PurpleConversation *conv, const char *name, const char *alias,
		const char *message, PurpleMessageFlags flags, time_t mtime);

#endif /*HAVE_CHATROOM_H_*/
