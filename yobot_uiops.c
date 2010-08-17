/*
 * yobot_uiops.c
 *
 *  Created on: Jul 16, 2010
 *      Author: mordy
 */
#include <purple.h>
#include "yobotproto.h"
#include "protoclient.h"
#include "yobot_ui.h"
#include "yobot_blist.h"
#include <string.h>
#include <glib.h>

#define register_signal(purple_component, signal, fn) \
	purple_signal_connect(purple_##purple_component##_get_handle(),\
			signal,\
			&handle, \
			PURPLE_CALLBACK(fn), \
			NULL);


/*needed because acct->gc is NULL until connected*/
void event_account_send(PurpleAccount *acct, yobot_proto_evtype evtype,
		yobot_proto_event event, void *txt) {
	struct yobot_eventinfo info;
	memset(&info, 0, sizeof(info));
	info.event = event;
	info.purple_type = YOBOT_PURPLE_ACCOUNT;
	info.severity = evtype;
	info.acctid = yobot_get_acct_id(acct);
	info.data = txt;
	info.len = (txt) ? strlen(txt) + 1 : 0;

	yobot_protoclient_event_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD);
}

static void event_connection_send(PurpleConnection *gc, yobot_proto_evtype evtype,
		yobot_proto_event event, const void *txt)
{
	struct yobot_eventinfo info;
	memset(&info, 0, sizeof(info));
	info.event = event;
	info.purple_type = YOBOT_PURPLE_ACCOUNT;
	info.severity = evtype;
	info.acctid = yobot_get_acct_id(gc->account);
	info.data = txt;
	info.len = (txt) ? strlen(txt) + 1 : 0;

	yobot_protoclient_event_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD);
}
/*===================PurpleConnection=========================*/

static void connect_progress(PurpleConnection *gc, const char *text,
		size_t step, size_t step_count) {
	printf("%s: %s\n", __func__, (text) ? text : "...");
	event_connection_send(gc,YOBOT_INFO,YOBOT_EVENT_CONNECTING,text);
}

static void notice(PurpleConnection *gc, const char *text) {
	event_connection_send(gc,YOBOT_INFO,YOBOT_EVENT_NOTICE,text);
}

static void report_disconnect_reason(PurpleConnection *gc, PurpleConnectionError reason,
		const char *text) {

	yobot_proto_event evt;
	yobot_proto_evtype severity = YOBOT_WARN; /*default*/

	/*translate between purple and protocol codes*/
	 if (reason == PURPLE_CONNECTION_ERROR_AUTHENTICATION_FAILED||
			reason == PURPLE_CONNECTION_ERROR_AUTHENTICATION_IMPOSSIBLE) {
		evt = YOBOT_EVENT_AUTH_FAIL;
	} else if (reason == PURPLE_CONNECTION_ERROR_OTHER_ERROR) {
		evt = YOBOT_EVENT_LOGIN_ERR;
	} else {
		evt = YOBOT_EVENT_DISCONNECTED;
		severity = YOBOT_INFO;
	}
	 event_connection_send(gc, severity, evt, text);
}

static void connected(PurpleConnection *gc) {
	printf("%s: connected! sending event\n", __func__);
	event_connection_send(gc,YOBOT_INFO,YOBOT_EVENT_CONNECTED,NULL);
}

static void disconnected(PurpleConnection *gc) {
	printf("%s: disconnected! \n", __func__);
	event_connection_send(gc,YOBOT_INFO,YOBOT_EVENT_DISCONNECTED,NULL);
}

PurpleConnectionUiOps yobot_connection_uiops =
{
	connect_progress, /* connect_progress*/
	connected, /* connected */
	disconnected, /* disconnected*/
	notice,  /* notice*/
	NULL, /* report_disconnect*/
	NULL, /* network_connected */
	NULL, /* network_disconnected*/
	report_disconnect_reason,/* report_disconnect_reason */
	NULL,
	NULL,
	NULL
};

/*Signal Handlers*/

void yobot_connection_signals_register(void) {
}

/*================================PurpleAccount=============================*/

/*UiOps*/

static void status_changed(PurpleAccount *account, PurpleStatus *status) {
	int acctid = yobot_get_acct_id(account);
	if (!acctid) {
		printf("%s: got null account. bailing!\n", __func__);
		return;
	}
	yobot_status_r ystatus = yobot_blist_get_status(status);
	yobot_blist_send_status_change(YOBOT_USER_SELF, ystatus, acctid);
}

void yobot_user_authorize(PurpleAccount *account, const char *user, gboolean accept) {
	account_uidata *priv = account->ui_data;
	if(!priv) {
		printf("%s: uidata missing\n", __func__);
		return;
	}
	authrequest *ar = g_hash_table_lookup(priv->requests, user);
	if(!ar) {
		printf("%s: can't find add request for user %s\n", __func__, user);
		printf("current entries...\n");
		GList *keys;
		for (keys = g_hash_table_get_keys(priv->requests); keys; keys = keys->next) {
			printf("KEY %s\n", (char*)keys->data);
		}
		return;
	}
	if (accept)
		ar->allow_cb(ar->user_data);
	else
		ar->deny_cb(ar->user_data);

	free(ar);
	g_hash_table_remove(priv->requests, user);
}

static void *request_authorize(PurpleAccount *account, const char *remote_user, const char *id,
		const char *alias, const char *message, gboolean on_list,
		PurpleAccountRequestAuthorizationCb authorize_cb, PurpleAccountRequestAuthorizationCb deny_cb,
		void *user_data) {
	if (on_list) {
		authorize_cb(user_data);
		return NULL;
	}
	/*sort our shit together*/
	authrequest *ar = malloc(sizeof(authrequest));

	ar->allow_cb = authorize_cb;
	ar->deny_cb = deny_cb;
	ar->user_data = user_data;

	account_uidata *priv = account->ui_data;
	if(!priv){
		printf("%s: couldn't get hash table!\n", __func__);
	}
	char *tmp = malloc(strlen(remote_user)+1);
	strcpy(tmp, remote_user);

	g_hash_table_insert(priv->requests, (gpointer)tmp, ar);
	printf("remote_user: %s\n", remote_user);
	GList *keys = g_hash_table_get_keys(priv->requests);
	for (; keys; keys = keys->next) {
		printf("%s: key: %s\n", __func__, (char*)keys->data);
	}

	/*send out an event*/
	struct yobot_eventinfo info;
	info.event = YOBOT_EVENT_USER_ADDREQ;
	info.acctid = yobot_get_acct_id(account);
	info.data = remote_user;
	info.len = strlen(remote_user) + 1;
	yobot_protoclient_event_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD);
	return NULL;
}
PurpleAccountUiOps yobot_account_uiops = {
		NULL, /*notify_added*/
		status_changed, /*status_changed, */
		NULL, /*request_add*/
		request_authorize, /*request_authorize*/
		NULL, /*close_account_request*/
};


/*Signal Handlers*/

static void account_added(PurpleAccount *account) {
	puts(__func__);
	int id = yobot_get_acct_id(account);
	g_hash_table_insert(yobot_acct_table,GINT_TO_POINTER(id),account);
	if (account->ui_data) {
		account_uidata *priv = account->ui_data;
		priv->requests = g_hash_table_new_full(g_str_hash, g_str_equal, free, NULL);
	}
	puts("inserted account into hash table");
	puts("sending event...");
	event_account_send(account,YOBOT_INFO,YOBOT_EVENT_ACCT_REGISTERED,NULL);
	puts("exited");
}

static void account_removed(PurpleAccount *account) {
	printf("%s: removing account %d\n", __func__, yobot_get_acct_id(account));
	g_hash_table_remove(yobot_acct_table,GINT_TO_POINTER(yobot_get_acct_id(account)));
	g_hash_table_destroy(((account_uidata*)account->ui_data)->requests);
	event_account_send(account,YOBOT_INFO,YOBOT_EVENT_ACCT_UNREGISTERED,NULL);
}


void yobot_account_signals_register(void) {
	int handle;
	register_signal(accounts, "account-added", account_added);
	register_signal(accounts, "account-removed", account_removed);
}
#undef register_signal

/******************************* notify ********************************/
static void *notify_message(PurpleNotifyMsgType type, const char *title, const char *primary,
		const char *secondary) {
	if (!title)
		title = "";
	if (!primary)
		primary = "";
	if(!secondary)
		secondary = "";
	char *retstr = g_strconcat(title, primary, secondary, NULL);
	printf("%s: %s\n",__func__,  retstr);
	g_free(retstr);
	struct yobot_eventinfo info;
	return NULL;
}
PurpleNotifyUiOps yobot_notify_uiops = {
		notify_message, /*notify_message*/
		NULL, /*notify_email*/
		NULL, /*notify_emails*/
		NULL, /*notify_formatted*/
		NULL, /*notify_searchresults*/
		NULL, /*notify_searchresults_new_rows*/
		NULL, /*notify_userinfo*/
		NULL, /*notify_uri*/
		NULL, /*close_notify*/
		NULL, /*reserved1*/
		NULL, /*reserved2*/
		NULL, /*reserved3*/
		NULL, /*Reserved4*/
};
