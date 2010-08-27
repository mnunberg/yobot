/*
 * yobot_request.c
 *
 *  Created on: Aug 24, 2010
 *      Author: mordy
 */
#include <purple.h>
#include <glib.h>
#include <string.h> /*memset*/
#include <stdlib.h> /*strtol*/
#include <limits.h> /*strtol*/
#include <errno.h> /*strtol*/
#include <stdarg.h>
#include "yobot_ui.h"
#include "yobotproto.h"
#include "protoclient.h"
#include "yobot_log.h"

/************************ request *********************************/
/*this is quite the same as an authrequest...*/
typedef struct {
	GHashTable *callbacks; /*hash tables indexed by options..
	special values for ok/cancel/input*/
	const gpointer *user_data;
	PurpleRequestType reqtype;
} genericrequest;

struct mkrequestopts {
	PurpleAccount *acct;
	const char *title;
	const char *primary;
	const char *secondary;
	const char *ok_text;
	const char *cancel_text;
	const void *user_data;
	GCallback ok_cb;
	GCallback cancel_cb;
	size_t cbcount;
#ifndef _WIN32
	va_list *callbacks;
#else
	/*apparently windows crt doesn't like us playing with va_list*/
	void **callbacks;
#endif
	PurpleRequestType reqtype;
};

typedef struct {
	PurpleAccount *acct;
	uint32_t reqref;
} request_handle;

#define MAX_OPTIONS 16
#ifdef _WIN32
static void **get_action_list(size_t count, va_list vl) {
	void **arr = malloc((sizeof(void*)*MAX_OPTIONS*2)+1);
	memset(arr,0, (sizeof(void*)*MAX_OPTIONS*2)+1);
	int i = 0;
	while(i < (MAX_OPTIONS*2) && (float)i/2 < count) {
		arr[i++] = va_arg(vl, void*);
		arr[i++] = va_arg(vl, void*);
	}
	arr[i] = NULL;
	yobot_log_debug("%d", i);
	return arr;
}
#endif

static uint32_t genkey(PurpleAccount *acct) {
	if(!acct) {
		yobot_log_err("account is NULL");
		return 0;
	}
	if(!acct->ui_data) {
		yobot_log_warn("can't find account_uidata.. ");
		return 0;
	}
	account_uidata *priv = acct->ui_data;
	if(priv->greq_key == UINT32_MAX -1) {
		yobot_log_err("Excceded request count.. will start deleting..");
		priv->greq_key = 0;
	}
	priv->greq_key++;
	g_hash_table_remove(priv->general_requests, GINT_TO_POINTER(priv->greq_key));
	yobot_log_debug("(re)using key %d from requests hash table for account %d",
			priv->greq_key, yobot_get_acct_id(acct));
	return priv->greq_key;
}

static void mkrequestopts_defaults(struct mkrequestopts *reqopts,
		const char *title, const char *primary, const char *secondary,
		PurpleAccount *account) {
	memset(reqopts, 0, sizeof(struct mkrequestopts));
	if(!primary) primary = "";
	if(!title) title = "";
	if(!secondary) secondary="";
	reqopts->acct = account;
	reqopts->title = g_markup_escape_text(title, -1);
	reqopts->primary = g_markup_escape_text(primary, -1);
	reqopts->secondary = g_markup_escape_text(secondary, -1);
}
static void *handle_send_request(struct mkrequestopts *reqopts) {
	yobot_purple_account_context_printf();
	/*build simple XML string*/
	GString *xmlstring = g_string_new(NULL);
	g_string_append_printf(xmlstring, "<request title='%s' primary='%s' secondary='%s' type='%d'>",
			reqopts->title, reqopts->primary, reqopts->secondary, reqopts->reqtype);
	genericrequest *privreq = g_malloc0(sizeof(genericrequest));
	privreq->reqtype = reqopts->reqtype;
	privreq->callbacks = g_hash_table_new(g_direct_hash, g_direct_equal);
	privreq->user_data = reqopts->user_data;

	const char *xmloptfmt = "<option text='%s' return='%d'/>";
	if (reqopts->cancel_cb) {
		g_string_append_printf(xmlstring, xmloptfmt, reqopts->cancel_text,
				YOBOT_REQUEST_CANCEL);
		g_hash_table_insert(privreq->callbacks,
				GINT_TO_POINTER(YOBOT_REQUEST_CANCEL), reqopts->cancel_cb);
	}
	if (reqopts->ok_cb) {
		g_string_append_printf(xmlstring, xmloptfmt, reqopts->cancel_text,
				YOBOT_REQUEST_OK);
		g_hash_table_insert(privreq->callbacks,
				GINT_TO_POINTER(YOBOT_REQUEST_OK),reqopts->ok_cb);
	}
	if (reqopts->callbacks) {
#ifndef _WIN32
		int i;
		for(i=0; i < reqopts->cbcount; i++) {
			char *tmp = va_arg(*(reqopts->callbacks), char*);
			void *cb = va_arg(*(reqopts->callbacks),
					void*);
			g_string_append_printf(xmlstring, xmloptfmt, tmp, i);
			g_hash_table_insert(privreq->callbacks, GINT_TO_POINTER(i), cb);
		}
#else
		int i=0;
		while(i < (MAX_OPTIONS*2) && (float)i/2 < reqopts->cbcount ) {
			g_string_append_printf(xmlstring, xmloptfmt, (char*) reqopts->callbacks[i], i);
			yobot_log_debug("appended");
			g_hash_table_insert(privreq->callbacks, GINT_TO_POINTER(i), reqopts->callbacks[i+1]);
			i+=2;
		}
#endif
	}
	yobot_log_debug("done");
	g_string_append(xmlstring, "</request>");

	/*get the account, if there is one*/
	if (!reqopts->acct) {
		yobot_log_warn("passed NULL account.. trying context variable");
		if(!(reqopts->acct = yobot_purple_account_context_get())) {
			yobot_log_err("context is NULL. trouble ahead");
		}
	}
	/*get a key*/
	uint32_t key = genkey(reqopts->acct);
	if(!key) {
		yobot_log_err("key is empty.. trouble ahead");
		return NULL;
	}
	account_uidata *acctpriv = reqopts->acct->ui_data;
	/*insert into hash table.. we will reference this key when we respond*/
	g_hash_table_insert(acctpriv->general_requests, GINT_TO_POINTER(key), privreq);
	struct yobot_eventinfo info;
	memset(&info, 0, sizeof(info));
	info.reference = key;
	info.event = YOBOT_EVENT_PURPLE_REQUEST_GENERIC;
	info.data = xmlstring->str;
	info.len = xmlstring->len +1;
	info.acctid = yobot_get_acct_id(reqopts->acct);
	yobot_protoclient_event_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD);
	g_string_free(xmlstring, TRUE);

	request_handle *ret = g_new0(request_handle, 1);
	ret->acct = reqopts->acct;
	ret->reqref = key;
	/*finally, increase the reference count*/
	yobot_purple_account_refcount_increase(reqopts->acct);
	return (void*)ret;
}

void yobot_request_handle_response(PurpleAccount *acct, char *data, uint32_t reqref) {
	/*simply find the callback and call it with the userdata*/
	if(!data) {
		yobot_log_err("got null data");
		return;
	}
	long int option = strtol(data, NULL, 10);
	if(option == LONG_MAX || option == LONG_MIN) /*error*/ {
		yobot_log_err("strtol(option): %s", strerror(errno));
		return;
	}
	account_uidata *priv = acct->ui_data;
	if(!acct->ui_data) {
		yobot_log_err("ui_data is NULL!");
		return;
	}
	genericrequest *req = g_hash_table_lookup(
			priv->general_requests, GINT_TO_POINTER(reqref));
	if(!req) {
		yobot_log_err("wanted reference %d for account %d (%s) but found nothing",
				reqref, yobot_get_acct_id(acct), acct->username);
		return;
	}
	/*get callback, and call*/
	void *cb = g_hash_table_lookup(req->callbacks,
			GINT_TO_POINTER(option));
	if(!cb) {
		yobot_log_err("could not find action %d for request reference %d of account %d (%s)",
				option, reqref, yobot_get_acct_id(acct), acct->username);
		return;
	}
	switch (req->reqtype) {
	case PURPLE_REQUEST_ACTION: {
		((PurpleRequestActionCb)(cb))((void*)(req->user_data), (int)option);
		break;
	}
	case PURPLE_REQUEST_CHOICE: {
		((void(*)(void*,int))(cb))((void*)(req->user_data), option);
		break;
	default:
		yobot_log_warn("unhandled type %d", req->reqtype);
		break;
	}
	}
}

static void close_request(PurpleRequestType type, void *ui_handle) {
	yobot_log_warn("");
	request_handle *reqh = ui_handle;
	if(!reqh) {
		yobot_log_err("reqh NULL");
		return;
	}
	account_uidata *priv = reqh->acct->ui_data;
	genericrequest *greq = g_hash_table_lookup(
			priv->general_requests, GINT_TO_POINTER(reqh->reqref));
	if(!greq) {
		yobot_log_warn("couldn't find request %d in account %d (%s)",
				reqh->reqref, yobot_get_acct_id(reqh->acct),reqh->acct->username);
		yobot_purple_account_refcount_decrease(reqh->acct);
		return;
	}
	g_hash_table_destroy(greq->callbacks);
	g_hash_table_remove(priv->general_requests, GINT_TO_POINTER(reqh->reqref));
	free(greq);

	/*finally.. send an event*/
	struct yobot_eventinfo info;
	info.event = YOBOT_EVENT_PURPLE_REQUEST_GENERIC_CLOSED;
	info.acctid = yobot_get_acct_id(reqh->acct);
	info.reference = reqh->reqref;
	info.data = "HELLOWORLD";
	info.len = strlen("HELLOWORLD")+1;
	yobot_protoclient_event_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD);
	yobot_purple_account_refcount_decrease(reqh->acct);
	free(ui_handle);
}

static void *request_input(const char *title, const char *primary, const char *secondary,
		const char *default_value, gboolean multiline, gboolean masked, gchar *hint,
		const char *ok_text, GCallback ok_cb, const char *cancel_text, GCallback cancel_cb,
		PurpleAccount *account, const char *who, PurpleConversation *conv, void *user_data)  {
	yobot_log_warn("");
	return NULL;
}
static void *request_choice(const char *title, const char *primary, const char *secondary,
		int default_value, const char *ok_text, GCallback ok_cb, const char *cancel_text,
		GCallback cancel_cb, PurpleAccount *account, const char *who, PurpleConversation *conv,
		void *user_data, va_list choices) {
	yobot_log_warn("");
	return NULL;
}
static void *request_action(const char *title, const char *primary, const char *secondary,
		int default_action, PurpleAccount *account, const char *who, PurpleConversation *conv,
		void *user_data, size_t action_count, va_list actions) {
	struct mkrequestopts rops;
	mkrequestopts_defaults(&rops, title, primary, secondary, account);
	void *ret;
	rops.cbcount = action_count;
#ifndef _WIN32
	rops.callbacks = actions;
#else
	rops.callbacks = get_action_list(action_count, actions);
#endif
	rops.user_data = user_data;
	rops.reqtype = PURPLE_REQUEST_ACTION;
	ret = handle_send_request(&rops);
	return ret;
}
static void *request_fields(const char *title, const char *primary, const char *secondary,
		PurpleRequestFields *fields, const char *ok_text, GCallback ok_cb, const char *cancel_text,
		GCallback cancel_cb, PurpleAccount *account, const char *who,
		PurpleConversation *conv, void *user_data) {
	yobot_log_warn("");
	return NULL;
}
static void *request_file(const char *title, const char *filename, gboolean savedialog,
		GCallback ok_cb, GCallback cancel_cb, PurpleAccount *account, const char *who,
		PurpleConversation *conv, void *user_data) {
	yobot_log_debug("");
	return NULL;
}
static void *request_folder(const char *title, const char *dirname, GCallback ok_cb,
		GCallback cancel_cb, PurpleAccount *account, const char *who,
		PurpleConversation *conv, void *user_data) {
	yobot_log_warn("");
	return NULL;
}

PurpleRequestUiOps yobot_request_uiops = {
		request_input, /*request_input*/
		request_choice, /*request_choice*/
		request_action, /*request_action*/
		request_fields, /*request_fields*/
		request_file, /*request_file*/
		close_request, /*close_request*/
		request_folder, /*request_folder*/
		NULL, /*reserved1*/
		NULL, /*reserved2*/
		NULL, /*reserved3*/
		NULL, /*reserved4*/
};
