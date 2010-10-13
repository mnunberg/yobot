/*
 * yobot_conversation.c
 *
 *  Created on: Jul 16, 2010
 *      Author: mordy
 */

#include <purple.h>
#include "yobotproto.h"
#include "protoclient.h"
#include "yobot_ui.h"
#include "yobot_log.h"
#include <time.h>
#include <string.h>
#include <assert.h>
static void event_conversation_send(PurpleConversation *conv, yobot_proto_evtype evtype,
		yobot_proto_event event) {
	struct yobot_eventinfo info;
	memset(&info, 0, sizeof(info));
	info.event = event;
	info.severity = evtype;
	info.acctid = yobot_get_acct_id(conv->account);
	info.purple_type = YOBOT_PURPLE_CONV;
	info.data = conv->name;
	info.len = strlen(conv->name)+1;
	yobot_protoclient_event_encode(info, &server_write_fd,YOBOT_PROTOCLIENT_TO_FD);
}


static void create_conversation(PurpleConversation *conv) {
	char *type;
	if (conv->type == PURPLE_CONV_TYPE_CHAT) {
		type="chat";
	} else if (conv->type == PURPLE_CONV_TYPE_IM) {
		type="IM";
	} else {
		type="something else";
	}

	yobot_log_debug("name: %s, type=%s",conv->name, type);
}

static void write_chat(PurpleConversation *conv, const char *who,
		const char *message, PurpleMessageFlags flags, time_t mtime) {
	yobot_log_debug("<%s> %s", who, message);
	struct yobot_msginfo info;
	memset(&info, 0, sizeof(info));
	info.acctid = yobot_get_acct_id(conv->account);
	info.to = conv->name;
	info.txt = message;
	info.who = who;
	info.msgtime = mtime;
	info.commflags |= YOBOT_MSG_TYPE_CHAT;
	info.purple_flags = flags;

	yobot_protoclient_msg_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD);
}

static void write_conv(PurpleConversation *conv, const char *name,
		const char *alias, const char *message, PurpleMessageFlags flags,
		time_t mtime) {
	yobot_log_debug("[%d] %s: %s",flags,name,message);
	if (flags & PURPLE_MESSAGE_RECV) {
		struct yobot_msginfo info;
		memset(&info, 0, sizeof(info));
		info.acctid = yobot_get_acct_id(conv->account);
		info.to = conv->name;
		info.txt = message;
		info.who = name;
		info.msgtime = mtime;
		info.commflags = YOBOT_MSG_TYPE_IM;
		info.purple_flags = flags;
		yobot_protoclient_msg_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD);
	}
}

static void write_im(PurpleConversation *conv, const char *who,
		const char *message, PurpleMessageFlags flags, time_t mtime) {

	if (flags & PURPLE_MESSAGE_SEND) {
		who = purple_account_get_username(conv->account);
		if(!who) {
			yobot_log_err("WHO IS STILL NULL! WTF!");
			return;
		}
	} else if (flags & PURPLE_MESSAGE_RECV) {
		who = conv->name;
	} else {
		yobot_log_warn("can't handle flag %d", flags);
	}
	yobot_log_debug("who: %s, conv->name: %s, msg: %s", who, conv->name, message);
	struct yobot_msginfo info;
	memset(&info, 0, sizeof(info));
	info.acctid = yobot_get_acct_id(conv->account);
	info.to = conv->name;
	info.txt = message;
	info.who = who;
	info.msgtime = mtime;
	info.commflags = YOBOT_MSG_TYPE_IM;
	info.purple_flags = flags;

	yobot_protoclient_msg_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD);
}

#define leave_join(action, conv, user_name) \
	char *room_user = g_strconcat(conv->name, YOBOT_TEXT_DELIM, user_name, NULL); \
	struct yobot_eventinfo info; memset(&info, 0, sizeof(info)); \
	info.data = room_user; \
	info.event = action; \
	info.len = strlen(room_user) + 1; \
	info.acctid = yobot_get_acct_id(conv->account); \
	yobot_protoclient_event_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD); \
	g_free(room_user);

static void chat_add_users(PurpleConversation *conv, GList *cbuddies,
		gboolean _null) {
	 for (; cbuddies; cbuddies = cbuddies->next) {
		leave_join(YOBOT_EVENT_ROOM_USER_JOIN, conv,
				((PurpleConvChatBuddy*)cbuddies->data)->name);
	}
}

static void chat_remove_users(PurpleConversation  *conv, GList *users) {
	for (; users; users = users->next) {
		leave_join(YOBOT_EVENT_ROOM_USER_LEFT, conv, (char *)users->data);
	}
}

PurpleConversationUiOps yobot_conversation_uiops = {
		create_conversation, /*create_conversation*/
		NULL, /*destroy_conversation*/
		write_chat, /*write_chat*/
		write_im, /*write_im*/
		write_conv, /*write_conv*/
		chat_add_users, /*chat_add_users*/
		NULL, /*chat_rename_user*/
		chat_remove_users, /*chat_remove_users*/
		NULL, /*chat_update_user*/
		NULL, /*present*/
		NULL, /*has_focus*/
		NULL, /*custom_smiley_add*/
		NULL, /*custom_smiley_write*/
		NULL, /*custom_smiley_close*/
		NULL, /*send_confirm*/
		NULL, /*reserved1*/
		NULL, /*reserved2*/
		NULL, /*reserved3*/
		NULL  /*reserved4*/
};

/*Signal callbacks*/
static void chat_joined(PurpleConversation *conv) {
	yobot_log_info("joined room %s", conv->name);
	event_conversation_send(conv,YOBOT_INFO,YOBOT_EVENT_ROOM_JOINED);
}

static void chat_join_failed(PurpleConnection *gc, GHashTable *components) {
	struct yobot_eventinfo info;
	memset(&info, 0, sizeof(info));
	info.event = YOBOT_EVENT_ROOM_JOIN_FAILED;
	info.purple_type = YOBOT_PURPLE_CONV;
	info.severity = YOBOT_WARN;
	info.acctid = yobot_get_acct_id(gc->account);
	yobot_protoclient_event_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD);
}

static void sending_chat_msg(PurpleAccount *account, char **message, int id) {
}

static void sent_chat_msg(PurpleAccount *gc, const char *message, int id) {
}

static void received_chat_msg(PurpleAccount *account, char *sender, char *message,
                              PurpleConversation *conv, PurpleMessageFlags flags) {
	yobot_log_info("Sender: %s", sender);
}


static void chat_left(PurpleConversation *conv) {
	event_conversation_send(conv,YOBOT_INFO,YOBOT_EVENT_ROOM_LEFT);
}


void yobot_conversation_signals_register(void) {
#define conv_add_signal(sig,f) purple_signal_connect(\
		purple_conversations_get_handle(), \
		sig, \
		&handle, \
		PURPLE_CALLBACK(f), \
		NULL);
	int handle;
	conv_add_signal("chat-join-failed",chat_join_failed);
	conv_add_signal("chat-joined", chat_joined);
	conv_add_signal("sending-chat-msg", sending_chat_msg);
	conv_add_signal("sent-chat-msg", sent_chat_msg);
	conv_add_signal("chat-left", chat_left);
	conv_add_signal("received-chat-msg", received_chat_msg);
#undef conv_add_signal
}
