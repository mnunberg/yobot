#include <purple.h>
#include <glib.h>
#include <stdio.h>
#include <string.h> /*memset*/
#include <errno.h>
#include <assert.h>
#include <limits.h>

#include <unistd.h>

/*For initiating the connection*/
#include <fcntl.h>

#include "yobot_ui.h"
#include "yobotproto.h"
#include "yobotutil.h"
#include "protoclient.h"
#include "yobot_blist.h"
#include "yobot_log.h"

#define conv_send(conv,msg) \
	if (purple_conversation_get_type(conv) == PURPLE_CONV_TYPE_CHAT) { \
		purple_conv_chat_send(conv->u.chat,msg); puts("purple_conv_chat_send called"); } \
	else { purple_conv_im_send(conv->u.im,msg); puts("purple_conv_im_send called"); }

#include "contrib/tpl.h"

extern tpl_hook_t tpl_hook;

/*Some internal structures used by our functions*/

/*satisfying some externs*/
int client_write_fd;
int server_write_fd;
GHashTable *yobot_acct_table;
GHashTable *yobot_request_table;


/*private functions*/
static void cmd_handler(yobot_protoclient_segment *seg);
static void join_chat(char *room_name, PurpleConnection *gc);
static void init_listener(gboolean first_time);
static void yobot_listener(gpointer _null, gint fd, PurpleInputCondition cond);



void yobot_core_ui_init()
{
	yobot_log_debug("begin");
	yobot_acct_table = g_hash_table_new(g_direct_hash, g_direct_equal);
	yobot_request_table = g_hash_table_new(g_direct_hash, g_direct_equal);
	yobot_purple_account_refcount = g_hash_table_new_full(g_direct_hash,
			g_direct_equal, NULL, free);

	/*Set UiOps*/
	purple_connections_set_ui_ops(&yobot_connection_uiops);
	purple_conversations_set_ui_ops(&yobot_conversation_uiops);
	purple_accounts_set_ui_ops(&yobot_account_uiops);
	purple_blist_set_ui_ops(&yobot_blist_uiops);
	purple_request_set_ui_ops(&yobot_request_uiops);
	purple_notify_set_ui_ops(&yobot_notify_uiops);


	/*Connect signal handlers.. each module should implement its own wrapper*/
	yobot_account_signals_register();
	yobot_conversation_signals_register();
	yobot_connection_signals_register();
	yobot_blist_signals_register();
	/*...*/
	yobot_proto_setlogger(yobot_log_params.prefix);
	init_listener(TRUE);
}

int *yobot_purple_account_refcount_get(PurpleAccount *acct) {
	int *tmp = g_hash_table_lookup(yobot_purple_account_refcount, acct);
	if(!tmp) /*NULL POINTER*/ {
		yobot_log_err("got null value for refcount - for acct ptr %p", acct);
	}
	return tmp;
}

int *yobot_purple_account_refcount_decrease(PurpleAccount *acct) {
	int *tmp = yobot_purple_account_refcount_get(acct);
	if(!tmp) {
		yobot_log_err("refcount is already null for %p", acct);
		return tmp;
	}
	(*tmp)--;
	if(*tmp == 0) {
		purple_account_destroy(acct);
		g_hash_table_destroy(((account_uidata*)acct->ui_data)->buddy_requests);
		g_hash_table_destroy(((account_uidata*)acct->ui_data)->general_requests);
	}
	return tmp;
}

int *yobot_purple_account_refcount_increase(PurpleAccount *acct) {
	int *tmp = yobot_purple_account_refcount_get(acct);
	if(!tmp) {
		yobot_log_err("refcount is null for acct %p", acct);
		return tmp;
	}
	(*tmp)++;
	yobot_log_debug("tmp is now %d", *tmp);
	return tmp;
}

int *yobot_purple_account_refcount_register(PurpleAccount *acct) {
	yobot_log_debug("adding account %p to the refcount table", acct);
	int *tmp = malloc(sizeof(int));
	*tmp = 0;
	g_hash_table_insert(yobot_purple_account_refcount, acct, tmp);
	return tmp;

}

static void join_chat(char *room_name, PurpleConnection *gc) {
	/*check if chat already exists...*/
	if(purple_find_conversation_with_account(PURPLE_CONV_TYPE_CHAT, room_name, gc->account)) {
		/*exists, return success...*/
		struct yobot_eventinfo info;
		memset(&info,0,sizeof(info));
		info.event = YOBOT_EVENT_ROOM_JOINED;
		info.acctid = yobot_get_acct_id(gc->account);
		info.data = room_name;
		info.len = strlen(room_name) + 1;
		yobot_protoclient_event_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD);
		return;
	}
	if(!gc) {
		yobot_log_err("Connection is null for account. Not joining");
		return;
	}
	PurplePlugin *prpl = purple_connection_get_prpl(gc);
	if(!prpl) {
		yobot_log_err("Couldn't get prpl");
		return;
	}
	PurplePluginProtocolInfo *prpl_info = PURPLE_PLUGIN_PROTOCOL_INFO(prpl);
	if(!prpl_info) {
		yobot_log_err("prpl_info is null");
		return;
	}
	GHashTable *components = prpl_info->chat_info_defaults(gc, room_name);
	if(!components) {
		yobot_log_err("Couldn't get chat components");
		return;
	}
	serv_join_chat(gc, components);
}


static void init_listener(gboolean first_time)
{
	yobot_proto_segfrombuf(yobot_log_params.prefix);
	yobot_log_info("BEGIN");
#ifndef WIN32
	tpl_hook.oops = printf;
#endif
	/*Initialize the pipes*/
	int in, out, in_w;
	static guint cb_handle;
	static int s, yobot_socket;
	struct sockaddr_storage incoming_addr;
#ifdef WIN32
	if (first_time) {
		WSADATA wsadata;
		if(WSAStartup(MAKEWORD(2,0), &wsadata)!=0) {
			fprintf(stderr, "WSAStartup Failed!\n");
			exit(1);
		}
	}
#endif

	int status;

	/*remove all the accounts first...*/
	GList *accounts = purple_accounts_get_all();
	for (; accounts; accounts = accounts->next) {
		purple_accounts_remove((PurpleAccount*)accounts->data);
	}

	/*initialize the listening socket*/
	if (first_time == TRUE) {
		/*called first time only*/
		struct addrinfo hints;
		struct addrinfo *result;

		memset(&hints, 0, sizeof(struct addrinfo));
		hints.ai_family = AF_INET;
		hints.ai_socktype = SOCK_STREAM;
		hints.ai_next = NULL;

		status = getaddrinfo("localhost", "7771", &hints, &result);
		if (status < 0)
			perror("getaddrinfo");
		s = socket(result->ai_family, result->ai_socktype, result->ai_protocol);
		if (s < 0)
			perror("socket");
#ifndef _WIN32
		unsigned int opt = 1;
#else
		char opt = 1;
#endif
		status = setsockopt(s,SOL_SOCKET,SO_REUSEADDR,&opt,sizeof(opt));
		if (status < 0)
			perror("setsockopt");

		status = bind(s, result->ai_addr, result->ai_addrlen);
		if (status < 0)
			perror("bind");

		freeaddrinfo(result);
		status = listen(s, 5);
	}
	else {
		/*we need to close the old socket first*/
		purple_input_remove(cb_handle);
		close(yobot_socket);
	}

	/*block....*/
	socklen_t addr_size = sizeof incoming_addr;
	must_succeed(yobot_socket = accept(s,(struct sockaddr*)&incoming_addr,
			&addr_size));
	/*don't block anymore*/

	/*write a hello message*/
	struct yobot_eventinfo info;
	memset(&info, 0, sizeof(info));
	info.event = YOBOT_EVENT_CLIENT_REGISTERED;
	info.purple_type = YOBOT_CLIENT_INTERNAL;
	info.severity = YOBOT_INFO;
	yobot_protoclient_event_encode(info, &yobot_socket, YOBOT_PROTOCLIENT_TO_FD);


	//status = fcntl(yobot_socket,F_SETFL, flags|O_NONBLOCK);
	YOBOT_SET_SOCK_BLOCK(yobot_socket, 1, status);
	if(status <= -1 ) {
		perror(__func__);
		yobot_log_crit("fcntl failed");
	}

	in = in_w = out = yobot_socket;

	client_write_fd = in;
	server_write_fd = out;

	cb_handle = purple_input_add(in,
			PURPLE_INPUT_READ,
			yobot_listener,NULL);
	yobot_log_info("END");

}

static void yobot_listener(gpointer _null, gint fd, PurpleInputCondition cond)
{
	yobot_log_debug("BEGIN");
	struct segment_r segr;
	yobot_protoclient_segment *seg = NULL;
	segr = yobot_proto_read_segment(&fd);
	int old_errno = errno;
	if(!(segr.len)) {
		yobot_log_warn("segr.len is empty... empty read, going to error");
		goto err;
	}

	seg = yobot_protoclient_segment_decode(segr);
	segr.data = NULL;
	if(!seg) {
		yobot_log_warn("got NULL decoded segment");
		goto err;
	}

	if(seg->struct_type == YOBOT_PROTOCLIENT_CMD_SIMPLE ||
			seg->struct_type == YOBOT_PROTOCLIENT_YCMDI ||
			seg->struct_type == YOBOT_PROTOCLIENT_YMSGI ||
			seg->struct_type == YOBOT_PROTOCLIENT_YMKACCTI)
		cmd_handler(seg);
	else
		yobot_log_err("unsupported transmission");

	yobot_protoclient_free_segment(seg);
	return;

	err:
	if(old_errno && !(old_errno == EAGAIN || old_errno == EWOULDBLOCK)) {
		yobot_log_err("read error: %s", strerror(old_errno));
	}

	yobot_protoclient_free_segment(seg);
	if(segr.data)
		free(segr.data);

	init_listener(FALSE);
	return;
}

static void cmd_handler(yobot_protoclient_segment *seg) {
	/*Some stuff almost everything uses*/
	yobotcmd cmd;
	yobotcmd_internal *yci = seg->cmdi;
	cmd = *(yci->cmd);
	yobotcomm *comm = seg->comm;

	PurpleAccount *account = get_acct_from_id(cmd.acct_id);
	PurpleConnection *gc = NULL;

	if (account) {
		yobot_purple_account_context_set(account);
		gc = purple_account_get_connection(account);
		if (!gc) {
			if (!(
					cmd.command == YOBOT_CMD_ACCT_ENABLE||
					cmd.command == YOBOT_CMD_ACCT_NEW ||
					cmd.command == YOBOT_CMD_ACCT_REMOVE
					)) {
				yobot_log_warn(" (command %d): Got NULL connection for account %d",
						cmd.command, cmd.acct_id);
				if (comm->reference) {
					struct yobot_eventinfo info;
					memset(&info, 0, sizeof(info));
					info.commflags = YOBOT_RESPONSE_END;
					info.data = "Could not find the account requested";
					info.acctid = cmd.acct_id;
					info.severity = YOBOT_WARN;
					info.len = strlen(info.data);
					info.event = YOBOT_EVENT_ERR;
					yobot_protoclient_event_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD);
				}
				return;
			}
		}
	} else {
		if(cmd.command != YOBOT_CMD_ACCT_NEW) {
			yobot_log_err(" (command %d): Could not find account %d. Possible trouble ahead",
				cmd.command, cmd.acct_id);
		}
	}
	yobot_log_debug("got command %d", cmd.command);
	switch (cmd.command) {
	case YOBOT_CMD_ROOM_JOIN: {
		char *room_name = yci->data;
		join_chat(room_name, gc);
		break;
	}
	case YOBOT_CMD_ROOM_LEAVE: {
		char *room_name = yci->data;
		PurpleConversation *conv = purple_find_conversation_with_account(
				PURPLE_CONV_TYPE_CHAT, room_name, account);
		if(!conv) {
			yobot_log_warn("got request to leave room %s which we are not joined to",
					room_name);
			return;
		}
		purple_conversation_destroy(conv);
		break;
	}
	case YOBOT_CMD_MSG_SEND: {
		yobotmsg_internal *ymi = seg->msgi;
		PurpleConversation *conv;
		const char *destination = ymi->to;
		const char *msgbody = ymi->txt;

		if (comm->flags & YOBOT_MSG_ATTENTION) {
			serv_send_attention(gc,destination, 0);
			break;
		}

		conv = purple_find_conversation_with_account(
				yobot_proto_get_conv_type(comm->flags), destination,
				account);

		if (!conv) {
			if (comm->flags & YOBOT_MSG_TYPE_CHAT) {
				yobot_log_warn(" (acct %d) trying to send message to room %s which is not joined",
						cmd.acct_id, destination);
				//TODO: notify the client
				break;
				/*bail -- no such conversation, we'll bother the client to re-join
				 * if we're sure*/
			}
			conv = purple_conversation_new(PURPLE_CONV_TYPE_IM, account,
					destination);
			if (!conv) {
				puts("couldn't create conversation! BAILING!!!");
				break;
			}
		}
		conv_send(conv, msgbody);
		break;
	}

	case YOBOT_CMD_ACCT_NEW: {
		yobot_log_info("YOBOT_CMD_ACCT_NEW");
		const char *name, *pass;
		yobotmkacct_internal *ymkaccti = seg->mkaccti;
		name = ymkaccti->user;
		pass = ymkaccti->pass;
		yobot_log_info("new user: %s, proto %s",
				name, yobot_proto_get_prpl_id(ymkaccti->yomkacct->improto));
		yobot_log_debug("calling purple_acount_new");

		PurpleAccount *acct = purple_account_new(name,
				yobot_proto_get_prpl_id(ymkaccti->yomkacct->improto));
		yobot_purple_account_refcount_register(acct);
		yobot_purple_account_refcount_increase(acct);
		yobot_purple_account_context_set(acct);
		yobot_log_debug("done.. now setting up account ui data");
		purple_account_set_password(acct, pass);
		account_uidata *tmp = malloc(sizeof(account_uidata));
		tmp->id = cmd.acct_id;
		acct->ui_data = tmp;
		purple_accounts_add(acct);
		yobot_log_debug("added account");
		break;
	}

	case YOBOT_CMD_ACCT_ENABLE: {
		yobot_log_info("YOBOT_CMD_ACCT_ENABLE");
		assert (cmd.len == 0);
		purple_account_set_enabled(account,"user",TRUE);
//		purple_account_connect(account);
		yobot_log_debug("account connecting...");
		break;
	}
	case YOBOT_CMD_ACCT_REMOVE: {
		yobot_log_info("YOBOT_CMD_ACCT_REMOVE");
		assert (cmd.len == 0);
		if(!account) {
			yobot_log_warn("account %d is NULL, not removing", cmd.acct_id);
		}
		purple_accounts_remove(account); /*remove ID too*/
		account_uidata *priv = account->ui_data;
		priv->id = 0;
		yobot_purple_account_refcount_decrease(account);
		yobot_log_debug("removed");
		break;
	}
	case YOBOT_CMD_ROOM_FETCH_USERS: {
		assert(yci->data);
		char *room = yci->data;
		GList *users;
		/*find corresponding conv*/
		PurpleConversation *conv;
		struct yobot_eventinfo info;
		memset(&info, 0, sizeof(info));
		info.acctid = cmd.acct_id;
		info.reference = comm->reference;
		info.severity = YOBOT_INFO;
		info.event = YOBOT_EVENT_ROOM_USER_JOIN;
		info.purple_type = YOBOT_PURPLE_ACCOUNT;
		conv = purple_find_conversation_with_account(
				PURPLE_CONV_TYPE_CHAT, room, account);
		if (!conv) {
			printf("%s: couldn't find room %s. can't fetch user list. \n",
					__func__, room);
			/*return a failure notice*/
			info.severity = YOBOT_WARN;
			info.data = "Room doesn't exist";
			info.len = strlen(info.data);
			yobot_protoclient_event_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD);
			return;
		}
		users = purple_conv_chat_get_users(conv->u.chat);
		info.commflags = YOBOT_RESPONSE;
		for (; users; users = users->next) {
			PurpleConvChatBuddy *chatbuddy = users->data;
			char *room_user = g_strconcat(room, YOBOT_TEXT_DELIM, chatbuddy->name, NULL);
			info.len = strlen(room_user) + 1;
			info.data = room_user;
			yobot_protoclient_event_encode(info, &server_write_fd,
					YOBOT_PROTOCLIENT_TO_FD);
			g_free(room_user);
			memset(&info, 0, sizeof(info));
		}
		info.commflags = YOBOT_RESPONSE_END;
		info.data = room;
		info.len = strlen(room);

		yobot_protoclient_event_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD);
		break;
	}

	case YOBOT_CMD_FETCH_BUDDIES: {
		GSList *buddies = purple_find_buddies(account, NULL);
		PurpleBuddy *buddy;
		yobot_status_r ystatus;
		memset(&ystatus, 0, sizeof(ystatus));

		for (; buddies; buddies = buddies->next) {
			buddy = buddies->data;
			ystatus = yobot_blist_get_status(
					purple_presence_get_active_status(buddy->presence));
			yobot_blist_send_status_change(buddy->name, ystatus, 0, YOBOT_RESPONSE,
					comm->reference, cmd.acct_id);
		}
		struct yobot_eventinfo info;
		memset(&info,0,sizeof(info));
		info.event = YOBOT_EVENT_DUMMY;
		info.commflags = YOBOT_RESPONSE_END;
		info.acctid = cmd.acct_id;
		info.reference = comm->reference;
		yobot_protoclient_event_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD);
		break;
	}
	case YOBOT_CMD_FETCH_BUDDY_ICONS: {
		GSList *buddies = purple_find_buddies(account, NULL);
		PurpleBuddy *buddy = NULL;
		for (; buddies; buddies = buddies->next) {
			buddy =  buddies->data;
			yobot_blist_send_icon(buddy, 0, YOBOT_RESPONSE, comm->reference, cmd.acct_id);
		}
		struct yobot_eventinfo info;
		memset(&info,0,sizeof(info));
		info.event = YOBOT_EVENT_DUMMY;
		info.commflags = YOBOT_RESPONSE_END;
		info.acctid = cmd.acct_id;
		info.reference = comm->reference;
		yobot_protoclient_event_encode(info, &server_write_fd, YOBOT_PROTOCLIENT_TO_FD);
		break;
	}

	case YOBOT_CMD_USER_AUTHORIZE_ADD_DENY:
	case YOBOT_CMD_USER_AUTHORIZE_ADD_ACCEPT: {
		/*get the user*/
		char *user = yci->data;
		if (cmd.command == YOBOT_CMD_USER_AUTHORIZE_ADD_ACCEPT)
			yobot_user_authorize(account, user, TRUE);
		else
			yobot_user_authorize(account, user, FALSE);
		break;
	}
	case YOBOT_CMD_USER_ADD: {
		PurpleBuddy *buddy = purple_buddy_new(account, yci->data, NULL);
		if(!buddy) {
			printf("%s: ADD: buddy is null... grrr\n", __func__);
			break;
		}
		purple_account_add_buddy(account, buddy);
		break;
	}
	case YOBOT_CMD_USER_REMOVE: {
		PurpleBuddy *buddy = purple_find_buddy(account, yci->data);
		if(!buddy) {
			printf("%s: REMOVE: buddy is null.. \n", __func__);
			break;
		}
		purple_account_remove_buddy(account, buddy, purple_buddy_get_group(buddy));
		break;
	}
	case YOBOT_CMD_PURPLE_REQUEST_GENERIC_RESPONSE: {
		yobot_log_info("YOBOT_CMD_PURPLE_REQUEST_GENERIC_RESPONSE");
		yobot_request_handle_response(account, yci->data, comm->reference);
		break;
	}
	default:
		yobot_log_warn("unknown command %d.\n", cmd.command);
		break;
	}
}
