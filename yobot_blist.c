/*
 * yobot_blist.c
 *
 *  Created on: Aug 8, 2010
 *      Author: mordy
 */

/*============================ blist ============================*/
#include <stdio.h>
#include <purple.h>
#include "yobotproto.h"
#include "protoclient.h"
#include <string.h>
#include "yobot_ui.h"
#include "yobot_blist.h"
#include <stdarg.h>

#define register_signal(purple_component, signal, fn) \
	purple_signal_connect(purple_##purple_component##_get_handle(),\
			signal,\
			&handle, \
			PURPLE_CALLBACK(fn), \
			NULL);

PurpleBlistUiOps yobot_blist_uiops = {
		NULL, /*new_list*/
		NULL, /*new_node*/
		NULL, /*show*/
		NULL, /*update*/
		NULL, /*remove*/
		NULL, /*destroy*/
		NULL, /*set_visible*/
		NULL, /*request_add_buddy*/
		NULL, /*request_add_chat*/
		NULL, /*Request_add_group*/
		NULL, /*save_node*/
		NULL, /*remove_node*/
		NULL, /*save_account*/
		NULL, /*reserved1*/
};
/*no UiOps here that we can use.. use signals*/

/*a helper...*/

void yobot_blist_send_status_change(char *user, yobot_status_r status,
		uint32_t acctid, ...) {
	gchar *user_status = g_strconcat(user, YOBOT_TEXT_DELIM, status.status_message,
			NULL);
	struct yobot_eventinfo info;
	memset(&info, 0, sizeof(info));
	if (!acctid) {
		va_list ap;
		va_start(ap, acctid);
		info.commflags = va_arg(ap, yobot_proto_flags);
		info.reference = va_arg(ap, int);
		info.acctid = va_arg(ap, uint32_t);
		va_end(ap);
	} else {
		info.acctid = acctid;
	}
	info.event = status.status_event;
	info.purple_type = YOBOT_PURPLE_ACCOUNT;
	info.severity = YOBOT_INFO;
	info.len = strlen(user_status) + 1;
	printf("%s: USER: %s\n", __func__, user_status);
	info.data = user_status;
	yobot_protoclient_event_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD);
	g_free(user_status);
}

void yobot_blist_send_icon(PurpleBuddy *buddy, uint32_t acctid, ...) {
#define _NAME_MAX 128
	PurpleBuddyIcon *icon;
	icon = buddy->icon;
	if(!icon)
		return;
	gconstpointer icon_data;
	size_t icon_len;
	size_t name_len = strlen(buddy->name);
	size_t buflen = 0;
	/*get icon size first...*/
	icon_data = purple_buddy_icon_get_data(buddy->icon, &icon_len);
	if ((!icon_data) ||
			(name_len /*buddy len*/ > _NAME_MAX) ||
			(icon_len > YOBOT_MAX_COMMSIZE - _NAME_MAX-1)) {
		fprintf(stderr, "%s:wtf.. icon is %p, length is %d, namelen is %d\n",
				__func__, icon_data, (int)icon_len, (int)name_len);
		return;
	}

	char *buf = g_malloc0(name_len + 1 + icon_len);
	char *bufptr = buf;
	memcpy(bufptr, buddy->name, name_len);
	buflen += name_len;
	bufptr += name_len;

	bufptr++;
	buflen++;

	*bufptr = YOBOT_TEXT_DELIM[0];

	bufptr++;
	buflen++;
	memcpy(bufptr, icon_data, icon_len);
	buflen += icon_len;

	struct yobot_eventinfo info;
	memset(&info, 0, sizeof(info));
	if(!acctid) {
		va_list ap;
		va_start(ap, acctid);
		info.commflags |= va_arg(ap, yobot_proto_flags);
		info.reference = va_arg(ap, int);
		info.acctid = va_arg(ap, uint32_t);
	} else {
		info.acctid = acctid;
	}
	info.event = YOBOT_EVENT_BUDDY_GOT_ICON;
	info.data = buf;
	info.commflags |= YOBOT_DATA_IS_BINARY;
	info.len = buflen;
	info.purple_type = YOBOT_PURPLE_ACCOUNT;
	info.severity = YOBOT_INFO;
	yobot_protoclient_event_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD);

	free(buf);
#undef _NAME_MAX
}

yobot_status_r yobot_blist_get_status(PurpleStatus *status) {
	yobot_status_r ret;
	memset(&ret, 0, sizeof(ret));

	PurpleStatusPrimitive primitive = purple_status_type_get_primitive(
			purple_status_get_type(status));
	yobot_proto_event evt = 0;
	switch (primitive) {
	case PURPLE_STATUS_AVAILABLE: /*online*/
		evt = YOBOT_EVENT_BUDDY_ONLINE;
		break;
	case PURPLE_STATUS_AWAY:
	case PURPLE_STATUS_EXTENDED_AWAY:
	case PURPLE_STATUS_UNAVAILABLE:
		evt = YOBOT_EVENT_BUDDY_AWAY;
		break;
	case PURPLE_STATUS_INVISIBLE:
		evt = YOBOT_EVENT_BUDDY_INVISIBLE;
		break;
	case PURPLE_STATUS_OFFLINE:
		evt = YOBOT_EVENT_BUDDY_OFFLINE;
		break;
	default:
		ret.is_fallback = 1;
		if (purple_status_is_online(status)) {
			evt = YOBOT_EVENT_BUDDY_ONLINE;
		} else {
			evt = YOBOT_EVENT_BUDDY_OFFLINE;
		}
	}
	ret.status_event = evt;
	ret.status_message = purple_status_get_attr_string(status, "message");
	return ret;
}

static void buddy_away(PurpleBuddy *buddy, PurpleStatus *old_status,
		PurpleStatus *status) {
	yobot_status_r ystatus = yobot_blist_get_status(status);
	if (ystatus.is_fallback) {
		ystatus.status_event = YOBOT_EVENT_BUDDY_AWAY;
	}
	yobot_blist_send_status_change(buddy->name, ystatus, yobot_get_acct_id(
			buddy->account));
}

static void buddy_idle(PurpleBuddy *buddy, gboolean old_idle, gboolean idle) {
	/*this is fucked up.. but anyway...*/
	yobot_proto_event evt;
	if (idle) {
		evt = YOBOT_EVENT_BUDDY_IDLE;
	} else {
		evt = YOBOT_EVENT_BUDDY_UNIDLE;
	}
	yobot_status_r ystatus;
	memset(&ystatus, 0, sizeof(ystatus));
	ystatus.status_event = evt;
	yobot_blist_send_status_change(buddy->name, ystatus, yobot_get_acct_id
			(buddy->account));
}

static void on_off_trigger(PurpleBuddy *buddy) {
	yobot_blist_send_status_change(buddy->name, yobot_blist_get_status(
			purple_presence_get_active_status(buddy->presence)),
			yobot_get_acct_id(buddy->account));
}

static void icon_changed(PurpleBuddy *buddy) {
	yobot_blist_send_icon(buddy, yobot_get_acct_id(buddy->account));
}

void yobot_blist_signals_register(void) {
	int handle;
	register_signal(blist, "buddy-status-changed", buddy_away);
	register_signal(blist, "buddy-idle-changed", buddy_idle);
	register_signal(blist, "buddy-signed-on", on_off_trigger);
	register_signal(blist, "buddy-signed-off", on_off_trigger);
	register_signal(blist, "buddy-icon-changed", icon_changed);
}

#undef register_signal
