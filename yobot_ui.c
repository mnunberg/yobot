#include <purple.h>
#include <glib.h>
#include <stdio.h>
#include <prpl.h>
#include <string.h> /*memset*/
#include <errno.h>
#include <assert.h>

#include <unistd.h>

/*For initiating the connection*/
#include <fcntl.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>

#include "yobot_ui.h"
#include "yobotproto.h"
#include "yobotutil.h"
#include "protoclient.h"
#include "yobot_blist.h"

#define BUFSIZE_MAX 32768
#define SMALLBUF_SIZE 128

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
	puts(__func__);
	yobot_acct_table = g_hash_table_new(g_direct_hash, g_direct_equal);
	yobot_request_table = g_hash_table_new(g_direct_hash, g_direct_equal);

	/*Set UiOps*/
	purple_connections_set_ui_ops(&yobot_connection_uiops);
	purple_conversations_set_ui_ops(&yobot_conversation_uiops);
	purple_accounts_set_ui_ops(&yobot_account_uiops);
	purple_blist_set_ui_ops(&yobot_blist_uiops);


	/*Connect signal handlers.. each module should implement its own wrapper*/
	yobot_account_signals_register();
	yobot_conversation_signals_register();
	yobot_connection_signals_register();
	yobot_blist_signals_register();
	/*...*/
	init_listener(TRUE);
}

static void join_chat(char *room_name, PurpleConnection *gc) {
	if(!gc) {
		printf("%s: gc is null! bailing!\n", __func__);
	}
	PurplePlugin *prpl = purple_connection_get_prpl(gc);
	if(!prpl) {
		puts("OOOPS! can't get prpl! bailing");
		exit(2);
	}
	PurplePluginProtocolInfo *prpl_info = PURPLE_PLUGIN_PROTOCOL_INFO(prpl);
	if(!prpl_info) {
		puts("oops! prpl_info is NULL! bailing!\n");
		exit(2);
	}
	GHashTable *components = prpl_info->chat_info_defaults(gc, room_name);
	if(!components) {
		printf("couldn't get components! bailing!\n");
		exit(2);
	}
	serv_join_chat(gc, components);
}


static void init_listener(gboolean first_time)
{
	puts(__func__);
	tpl_hook.oops = printf;
	/*Initialize the pipes*/
	int in, out, in_w;
	static guint cb_handle;
	static int s, yobot_socket;
	struct sockaddr_storage incoming_addr;

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

		unsigned int opt = 1;
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

	int flags = fcntl(yobot_socket, F_GETFL);

	status = fcntl(yobot_socket,F_SETFL, flags|O_NONBLOCK);
	if(status == -1 ) {
		perror(__func__);
		puts("fcntl error");
	}

	in = in_w = out = yobot_socket;

	client_write_fd = in;
	server_write_fd = out;

	cb_handle = purple_input_add(in,
			PURPLE_INPUT_READ,
			yobot_listener,NULL);
	puts("finished");
}

static void yobot_listener(gpointer _null, gint fd, PurpleInputCondition cond)
{
	puts(__func__);
	struct segment_r segr;
	yobot_protoclient_segment *seg = NULL;
	segr = yobot_proto_read_segment(&fd);
	int old_errno = errno;
	if(!(segr.len)) {
		puts("segr.len is 0");
		goto err;
	}

	seg = yobot_protoclient_segment_decode(segr);
	segr.data = NULL;
	if(!seg) {
		goto err;
		puts("segment is null");
	}

	if(seg->struct_type == YOBOT_PROTOCLIENT_CMD_SIMPLE ||
			seg->struct_type == YOBOT_PROTOCLIENT_YCMDI ||
			seg->struct_type == YOBOT_PROTOCLIENT_YMSGI ||
			seg->struct_type == YOBOT_PROTOCLIENT_YMKACCTI)
		cmd_handler(seg);
	else
		printf("%s: unsupported transmission. bailing!\n", __func__);

	yobot_protoclient_free_segment(seg);
	return;

	err:
	if(old_errno && !(old_errno == EAGAIN || old_errno == EWOULDBLOCK)) {
		printf("EAGAIN is %d, old errno is %d\n", EAGAIN, old_errno);
		fprintf(stderr, "%s(GRRR): %s\n", __func__, strerror(old_errno));
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
		gc = purple_account_get_connection(account);
		if (!gc) {
			if (!(cmd.command == YOBOT_CMD_ACCT_ENABLE||
					cmd.command == YOBOT_CMD_ACCT_NEW ||
					cmd.command == YOBOT_CMD_ACCT_REMOVE)) {
				printf("ERROR: command: %d\n", cmd.command);
				printf("%s: account %d not connected\n", __func__, cmd.acct_id);
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
	}
	printf("GOT COMMAND %d\n", cmd.command);
	switch (cmd.command) {
	case YOBOT_CMD_ROOM_JOIN: {
		puts("JOIN");
		char *room_name = yci->data;
		join_chat(room_name, gc);
		break;
	}

	case YOBOT_CMD_MSG_SEND: {
		puts("YOBOT_CMD_MSG_SEND");
		if(gc == NULL || account == NULL) {
			printf("%s: account=%p, gc=%p, bailing!\n",
					__func__, account, gc);
			break;
		}
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
				puts("Conversation does not exist..");
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
		puts("cmd_handler: YOBOT_CMD_ACCT_NEW");
		const char *name, *pass;
		yobotmkacct_internal *ymkaccti = seg->mkaccti;
		name = ymkaccti->user;
		pass = ymkaccti->pass;
		printf("%s: got username:%s, password %s, ID %d, improto %d\n", __func__, name, pass, cmd.acct_id, ymkaccti->yomkacct->improto);
		printf("prpl-id = %s\n", yobot_proto_get_prpl_id(ymkaccti->yomkacct->improto));
		puts("callign purple_account_new");
		PurpleAccount *acct = purple_account_new(name,
				yobot_proto_get_prpl_id(ymkaccti->yomkacct->improto));
		puts("done");
		purple_account_set_password(acct, pass);
		account_uidata *tmp = malloc(sizeof(account_uidata));
		tmp->id = cmd.acct_id;
		acct->ui_data = tmp;
		purple_accounts_add(acct);
		break;
		puts("done making account");
	}

	case YOBOT_CMD_ACCT_ENABLE: {
		puts("YOBOT_CMD_ACCT_ENABLE");
		assert (cmd.len == 0);
		purple_account_set_enabled(account,"user",TRUE);
		break;
	}
	case YOBOT_CMD_ACCT_REMOVE: {
		puts("YOBOT_CMD_ACCT_REMOVE");
		assert (cmd.len == 0);
		if(!account) {
			printf("%s: account is NULL, not removing\n", __func__);
		}
		purple_accounts_remove(account);
		puts("account removed");
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
			char *room_user = g_strconcat(room, YOBOT_TEXT_DELIM,
					(char*)users->data, NULL);
			info.len = strlen(room_user);
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
	default:
		printf("%s: unknown command %d.\n", __func__, cmd.command);
		break;
	}
}
