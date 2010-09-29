

#ifndef HAVE_YOBOT_UI_H_
#define HAVE_CHAROOM_H_
#include <purple.h>
#include <glib.h>
#include "yobotproto.h"
#include <stdarg.h>
#include <stdio.h>
#include <sys/types.h>

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

typedef struct {
	PurpleAccountRequestAuthorizationCb deny_cb;
	PurpleAccountRequestAuthorizationCb allow_cb;
	void *user_data;
} authrequest;


typedef struct {
	GHashTable *buddy_requests;
	GHashTable *general_requests;
	uint32_t id;
	uint32_t greq_key;
} account_uidata;

/*thanks to darkhippo/darkrain42 for pointing this out. this is a global fd
 * variable which is set whenever input is received, that way any subsequent
 * functions acting upon data received from this fd will be able to reference
 * the account simply by looking up the fd and then querying the table.. let's
 * hope this isn't broken
 */
extern int global_current_fd; /*main.c*/
extern PurpleAccount *global_current_account;
#define yobot_purple_account_context_set(acct) global_current_account = acct;
#define yobot_purple_account_context_get() global_current_account
#define yobot_purple_account_context_printf() ;/* \
	if (global_current_account) { yobot_log_err("CONTEXT: %s", global_current_account->username); \
	} else { yobot_log_err("CONTEXT: account is null"); } */

void yobot_core_ui_init(void);

/*To be filled in by the actual modules*/
extern void yobot_conversation_signals_register(void); /*yobot_conversation.c.. i think*/
extern void yobot_connection_signals_register(void); /*yobot_uiops.c*/
extern void yobot_account_signals_register(void); /*yobot_uiops.c*/
extern void yobot_blist_signals_register(void); /*yobot_uiops.c*/

extern void yobot_user_authorize(PurpleAccount *account, const char *user, gboolean accept);
void yobot_request_handle_response(PurpleAccount *acct, char *data, uint32_t reqref);

extern PurpleConnectionUiOps yobot_connection_uiops; /*yobot_uiops.c*/
extern PurpleConversationUiOps yobot_conversation_uiops; /*yobot_conversation.c*/
extern PurpleAccountUiOps yobot_account_uiops;
extern PurpleBlistUiOps yobot_blist_uiops; /*yobot_blist.c*/
extern PurpleDebugUiOps yobot_libpurple_debug_uiops;
extern PurpleRequestUiOps yobot_request_uiops;
extern PurpleNotifyUiOps yobot_notify_uiops;

/*implemented in yobot_ui.c*/
extern int client_write_fd;
extern int server_write_fd;
GHashTable *yobot_acct_table;
GHashTable *yobot_request_table;
GHashTable *yobot_purple_account_refcount;
/*note, this key is transient.. don't store it anywhere.
 * if it returns NULL, the account has been removed*/
int *yobot_purple_account_refcount_get(PurpleAccount *acct);
int *yobot_purple_account_refcount_decrease(PurpleAccount *acct);
int *yobot_purple_account_refcount_increase(PurpleAccount *acct);
int *yobot_purple_account_refcount_register(PurpleAccount *acct);

/*application mode, whether we are an actual daemon, or just invoked as
 * part of a desktop application, in which case we shut down after first exit
 */
typedef enum {
	YOBOT_DESKTOP,
	YOBOT_DAEMON
} yobot_application_modes;
extern int yobot_application_mode; /*initialized in main.c*/

/*address and port on which to listen*/
extern char *yobot_listen_address, *yobot_listen_port;

#endif /*HAVE_YOBOT_UI_H_*/
