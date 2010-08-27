/*
 * yobot_uiops.c
 *
 *  Created on: Jul 16, 2010
 *      Author: mordy
 */
#include <purple.h>
#include <string.h>
#include <glib.h>

#include "yobotproto.h"
#include "protoclient.h"
#include "yobot_ui.h"
#include "yobot_blist.h"
#include "yobot_log.h"

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
	yobot_log_debug((text) ? text : "...");
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
	yobot_log_info("%s connected", gc->account->username);
	event_connection_send(gc,YOBOT_INFO,YOBOT_EVENT_CONNECTED,NULL);
}

static void disconnected(PurpleConnection *gc) {
	yobot_log_info("%s disconnected", gc->account->username);
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
		yobot_log_warn("account ID is unknown");
		return;
	}
	yobot_status_r ystatus = yobot_blist_get_status(status);
	yobot_blist_send_status_change(YOBOT_USER_SELF, ystatus, acctid);
}

void yobot_user_authorize(PurpleAccount *account, const char *user, gboolean accept) {
	account_uidata *priv = account->ui_data;
	if(!priv) {
		yobot_log_err("uidata missing");
		return;
	}
	authrequest *ar = g_hash_table_lookup(priv->buddy_requests, user);
	if(!ar) {
		printf("%s: can't find add request for user %s\n", __func__, user);
		printf("current entries...\n");
		GList *keys;
		for (keys = g_hash_table_get_keys(priv->buddy_requests); keys; keys = keys->next) {
			printf("KEY %s\n", (char*)keys->data);
		}
		return;
	}
	if (accept)
		ar->allow_cb(ar->user_data);
	else
		ar->deny_cb(ar->user_data);

	free(ar);
	g_hash_table_remove(priv->buddy_requests, user);
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

	g_hash_table_insert(priv->buddy_requests, (gpointer)tmp, ar);
	printf("remote_user: %s\n", remote_user);
	GList *keys = g_hash_table_get_keys(priv->buddy_requests);
	for (; keys; keys = keys->next) {
		yobot_log_debug("key: %s\n",(char*)keys->data);
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
	int id = yobot_get_acct_id(account);
	g_hash_table_insert(yobot_acct_table,GINT_TO_POINTER(id),account);
	if (account->ui_data) {
		account_uidata *priv = account->ui_data;
		priv->buddy_requests = g_hash_table_new_full(g_str_hash, g_str_equal, free, NULL);
		priv->general_requests = g_hash_table_new(g_direct_hash, g_direct_equal);
		priv->greq_key = 0;
	}
	yobot_log_debug("inserted account [ID=%ld, name=%s] into hash table", id, account->username);
	event_account_send(account,YOBOT_INFO,YOBOT_EVENT_ACCT_REGISTERED,NULL);
}

static void account_removed(PurpleAccount *account) {
	yobot_log_debug("removing account %d", yobot_get_acct_id(account));
	g_hash_table_remove(yobot_acct_table,GINT_TO_POINTER(yobot_get_acct_id(account)));
	event_account_send(account,YOBOT_INFO,YOBOT_EVENT_ACCT_UNREGISTERED,NULL);
}

static void account_connecting(PurpleAccount *account) {
	yobot_log_warn("");
}

void yobot_account_signals_register(void) {
	int handle;
	register_signal(accounts, "account-added", account_added);
	register_signal(accounts, "account-removed", account_removed);
	register_signal(accounts, "account-connecting", account_connecting);
}
#undef register_signal

/******************************* notify ********************************/
/*for now, just wrap stuff*/
struct notice_params {
	const char *title;
	const char *primary;
	const char *secondary;
	const char *txt;
	const char *msg;
	const char *formatted;
	yobot_proto_evtype severity;
	PurpleAccount *acct;
};

static void send_notice(struct notice_params *params) {
	GString *xmlstring = g_string_new("");
	g_string_append_printf(xmlstring, "<notice title='%s' primary='%s' secondary='%s'>",
			params->title, params->primary, params->secondary);
	if(params->formatted) {
		g_string_append(xmlstring, params->formatted); }
	g_string_append(xmlstring, "</notice>");

	struct yobot_eventinfo info;
	memset(&info, 0, sizeof(info));
	if(!params->acct) { /*need context*/
		params->acct = yobot_purple_account_context_get();
		if(!params->acct) {
			yobot_log_err("account is NULL");
			g_string_free(xmlstring, TRUE);
			return;
		}
	}
	info.acctid = yobot_get_acct_id(params->acct);
	info.event = YOBOT_EVENT_PURPLE_NOTICE_GENERIC;
	info.data = xmlstring->str;
	info.len = xmlstring->len + 1;
	info.severity = params->severity;
	yobot_protoclient_event_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD);
	g_string_free(xmlstring, TRUE);
	return;
}
static void *notify_message(PurpleNotifyMsgType type, const char *title,
		const char *primary, const char *secondary) {
	if (!title)
		title = "";
	if (!primary)
		primary = "";
	if(!secondary)
		secondary = "";

	struct notice_params params;
	memset(&params, 0, sizeof(params));
	params.title = title;
	params.primary = primary;
	params.secondary = secondary;
	switch (type) {
	case PURPLE_NOTIFY_MSG_ERROR:
		params.severity = YOBOT_ERR;
		break;
	case PURPLE_NOTIFY_MSG_WARNING:
		params.severity = YOBOT_WARN;
		break;
	case PURPLE_NOTIFY_MSG_INFO:
		params.severity = YOBOT_INFO;
		break;
	default:
		break;
	}
	send_notice(&params);
	return NULL;
}
static void *notify_formatted(const char *title, const char *primary,
		const char *secondary, const char *text) {
	GString *tmp = g_string_new("<formatted>");
	g_string_append_printf(tmp, "%s</formatted>", text);
	struct notice_params params;
	memset(&params, 0, sizeof(params));
	params.title = title;
	params.primary = primary;
	params.secondary = secondary;
	params.txt = text;
	send_notice(&params);
	g_string_free(tmp, TRUE);
	return NULL;
}

static void *notify_userinfo(PurpleConnection *gc, const char *who,
		PurpleNotifyUserInfo *user_info) {
	/*this is the tough one.. get the variable fields..*/
	char *tmp = purple_notify_user_info_get_text_with_newline(user_info,YOBOT_TEXT_DELIM);
	GString *s = g_string_new("<entries");
	g_string_append_printf(s, "text='%s'/>", tmp);
	struct notice_params params;
	memset(&params, 0, sizeof(params));
	params.txt = s->str;
	params.acct = gc->account;
	send_notice(&params);
	g_string_free(s, TRUE);
	return NULL;
}
PurpleNotifyUiOps yobot_notify_uiops = {
		notify_message, /*notify_message*/
		NULL, /*notify_email*/
		NULL, /*notify_emails*/
		notify_formatted, /*notify_formatted*/
		NULL, /*notify_searchresults*/
		NULL, /*notify_searchresults_new_rows*/
		notify_userinfo, /*notify_userinfo*/
		NULL, /*notify_uri*/
		NULL, /*close_notify*/
		NULL, /*reserved1*/
		NULL, /*reserved2*/
		NULL, /*reserved3*/
		NULL, /*Reserved4*/
};

/************************ debug **********************************/
yobot_log_s yobot_libpurple_logparams = {
		"libpurple",
		1
};
static void libpurple_debug_print(PurpleDebugLevel level, const char *category, const char *arg_s) {
	static int output_to_console = -1;
	if(output_to_console < 0) {
		if(purple_debug_is_enabled()) {
			/*console output is enabled.. let's enable our own logging and then turn it off*/
			output_to_console = 1;
			purple_debug_set_enabled(FALSE);
		} else {
			output_to_console = 0;
		}
	}

	if(!output_to_console) {
		return;
	}
	char *stripped = strdup(arg_s);
	stripped[strlen(stripped)-1] = '\0';
	switch (level) {
	case PURPLE_DEBUG_ERROR:
		libpurple_log_err(stripped);
		break;
	case PURPLE_DEBUG_FATAL:
		libpurple_log_crit(stripped);
		break;
	case PURPLE_DEBUG_WARNING:
		libpurple_log_warn(stripped);
		break;
	case PURPLE_DEBUG_INFO:
		libpurple_log_info(stripped);
		break;

	default:
	case PURPLE_DEBUG_MISC:
		libpurple_log_debug(stripped);
		break;
	}
	free(stripped);
}
static gboolean libpurple_debug_is_enabled(PurpleDebugLevel level, const char *category) {
	return TRUE;
}
PurpleDebugUiOps yobot_libpurple_debug_uiops = {
	libpurple_debug_print, /*print*/
	libpurple_debug_is_enabled, /*is_enabled*/
	NULL, /*reserved1*/
	NULL, /*reserved2*/
	NULL, /*reserved3*/
	NULL, /*reserved4*/
};
