/*
 * Sample libpurple program written by Michael C. Brook (http://libpurple.com/)
 * (Some fragments taken from libpurple nullclient.c example found at http://pidgin.im/)
 */

#include "purple.h"
#include <glib.h>
#include <signal.h>
#include <stdio.h>
#include "yobot_ui.h"

#define CUSTOM_USER_DIRECTORY  "/tmp/yobot"
#define CUSTOM_PLUGIN_PATH     ""
#define PLUGIN_SAVE_PREF       "/purple/user/plugins/saved"
#define UI_ID                  "user"

#define must_succeed(f) if ((f)<=0) { perror(#f); exit(1); }

/**
 *  * The following eventloop functions are used in both pidgin and purple-text. If your
 *   * application uses glib mainloop, you can safely use this verbatim.
 *    */
#define PURPLE_GLIB_READ_COND  (G_IO_IN | G_IO_HUP | G_IO_ERR)
#define PURPLE_GLIB_WRITE_COND (G_IO_OUT | G_IO_HUP | G_IO_ERR | G_IO_NVAL)

typedef struct _PurpleGLibIOClosure {
	PurpleInputFunction function;
	guint result;
	gpointer data;
} PurpleGLibIOClosure;

typedef struct
{
	PurpleAccountRequestType type;
	PurpleAccount *account;
	void *ui_handle;
	char *user;
	gpointer userdata;
	PurpleAccountRequestAuthorizationCb auth_cb;
	PurpleAccountRequestAuthorizationCb deny_cb;
	guint ref;
} PurpleAccountRequestInfo;

static void purple_glib_io_destroy(gpointer data)
{
	g_free(data);
}

static gboolean purple_glib_io_invoke(GIOChannel *source, GIOCondition condition, gpointer data)
{
	PurpleGLibIOClosure *closure = data;
	PurpleInputCondition purple_cond = 0;

	if (condition & PURPLE_GLIB_READ_COND)
		purple_cond |= PURPLE_INPUT_READ;
	if (condition & PURPLE_GLIB_WRITE_COND)
		purple_cond |= PURPLE_INPUT_WRITE;
	closure->function(closure->data, g_io_channel_unix_get_fd(source),
			purple_cond);

	return TRUE;
}

static guint glib_input_add(gint fd, PurpleInputCondition condition, PurpleInputFunction function,
		gpointer data)
{
	PurpleGLibIOClosure *closure = g_new0(PurpleGLibIOClosure, 1);
	GIOChannel *channel;
	GIOCondition cond = 0;

	closure->function = function;
	closure->data = data;

	if (condition & PURPLE_INPUT_READ)
		cond |= PURPLE_GLIB_READ_COND;
	if (condition & PURPLE_INPUT_WRITE)
		cond |= PURPLE_GLIB_WRITE_COND;
	if (condition & YOBOT_LISTEN_COND)
		cond |= (G_IO_IN|G_IO_ERR);

	channel = g_io_channel_unix_new(fd);
	closure->result = g_io_add_watch_full(channel, G_PRIORITY_DEFAULT, cond,
			purple_glib_io_invoke, closure, purple_glib_io_destroy);

	g_io_channel_unref(channel);
	return closure->result;
}

static PurpleEventLoopUiOps glib_eventloops =
{
	g_timeout_add,
	g_source_remove,
	glib_input_add,
	g_source_remove,
	NULL,
#if GLIB_CHECK_VERSION(2,14,0)
	g_timeout_add_seconds,
#else
	NULL,
#endif

	/* padding */
	NULL,
	NULL,
	NULL
};
/*** End of the eventloop functions. ***/


static GHashTable *get_ui_info(void) {
	static GHashTable *info = NULL;
	if(!info)
		info = g_hash_table_new(g_str_hash, g_str_equal);
	g_hash_table_insert(info, "name", "YoBot");
	g_hash_table_insert(info, "version", "0.0.1");
	g_hash_table_insert(info, "website", "http://yobot.sourceforge.net");
	g_hash_table_insert(info, "client_type", "bot");
	return info;
}

static PurpleCoreUiOps core_uiops =
{
	NULL, /*prefs*/
	NULL, /*debug*/
	yobot_core_ui_init,
	NULL, /*quit*/
	get_ui_info,
	/* padding */
	NULL,
	NULL,
	NULL,
};


static void init_libpurple(debug)
{
	purple_util_set_user_dir(CUSTOM_USER_DIRECTORY);
	purple_debug_set_enabled(debug);

	purple_core_set_ui_ops(&core_uiops);

	purple_eventloop_set_ui_ops(&glib_eventloops);

	purple_plugins_add_search_path(CUSTOM_PLUGIN_PATH);

	if (!purple_core_init(UI_ID)) {
		fprintf(stderr,
				"libpurple initialization failed. Dumping core.\n"
				"Please report this!\n");
		abort();
	}
	purple_set_blist(purple_blist_new());
	purple_blist_load();
//	purple_buddy_icons_set_caching(TRUE);
//	purple_buddy_icons_set_cache_dir(CUSTOM_USER_DIRECTORY "/icons");
//	purple_prefs_load();
//	purple_plugins_load_saved(PLUGIN_SAVE_PREF);
	purple_pounces_load();
}


int main(int argc, char *argv[])
{
	if(argc < 2) {
		fprintf(stderr,"Need a debug parameter\n");
		exit(1);
	}
	/*get rid of annoying preferences*/
	remove(CUSTOM_USER_DIRECTORY "/prefs.xml");
	remove(CUSTOM_USER_DIRECTORY "/accounts.xml");
	remove(CUSTOM_USER_DIRECTORY "/status.xml");
	remove(CUSTOM_USER_DIRECTORY "/blist.xml");
	gboolean debug = atoi(argv[1]);
	GMainLoop *loop = g_main_loop_new(NULL, FALSE);
	signal(SIGCHLD, SIG_IGN);
	signal(SIGHUP, SIG_IGN);
//	signal(SIGPIPE, SIG_IGN);
	init_libpurple(debug);
	/*
	PurpleAccount *account = purple_account_new(ACCT_ID, "prpl-yahoo");
	purple_account_set_password(account, ACCT_PASS);
	purple_accounts_add(account);
	purple_account_set_enabled(account, UI_ID, TRUE);
	*/

	g_main_loop_run(loop);
	return 0;

}
