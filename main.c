/*
 * Sample libpurple program written by Michael C. Brook (http://libpurple.com/)
 * (Some fragments taken from libpurple nullclient.c example found at http://pidgin.im/)
 */

#include <purple.h>
#include <glib.h>
#include <signal.h>
#include <stdio.h>
#include "yobot_ui.h"
#include "yobot_log.h"
#include "win32/yobot_win32.h"
#include <errno.h>

#ifdef _WIN32
#include "win32/win32dep.h"
#include <windows.h>
#define PATHSEP "\\"
#define CUSTOM_USER_DIRECTORY  "C:" PATHSEP "temp" PATHSEP "yobot"
#define WPURPLE_ROOT "C:\\Program Files\\Pidgin"
#else
#define PATHSEP "/"
#define CUSTOM_USER_DIRECTORY PATHSEP "tmp" PATHSEP "yobot"
#endif

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

#if defined _WIN32
	channel = wpurple_g_io_channel_win32_new_socket(fd);
#else
	channel = g_io_channel_unix_new(fd);
#endif
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

#ifdef WIN32
	purple_plugins_add_search_path(WPURPLE_ROOT);
	purple_plugins_add_search_path(WPURPLE_ROOT PATHSEP "Plugins");
	purple_plugins_add_search_path(WPURPLE_ROOT PATHSEP "sasl2");
	purple_certificate_add_ca_search_path(WPURPLE_ROOT PATHSEP "ca-certs");
#endif
	if (!purple_core_init(UI_ID)) {
		fprintf(stderr,
				"libpurple initialization failed. Dumping core.\n"
				"Please report this!\n");
		abort();
	}
	purple_set_blist(purple_blist_new());
	purple_blist_load();
//	purple_prefs_load();
//	purple_plugins_load_saved(PLUGIN_SAVE_PREF);
	purple_pounces_load();
}


yobot_log_s yobot_log_params = {
		"Yobot-Purple",
		1
};

int main(int argc, char *argv[])
{
	if(argc < 2) {
		fprintf(stderr,"Need a debug parameter\n");
		exit(1);
	}
#ifdef _WIN32
	yobot_patch_purple_searchpath();
	yobot_log_info("testing.. ");
	const char *tmp = wpurple_install_dir();
	if (!tmp) {
		yobot_log_err("install_dir() returned NULL");
	}
	yobot_log_info("install_dir() returned %s", tmp);
	yobot_log_info("trying dependent wpurple_lib_dir");
	wpurple_lib_dir();

#endif
	/*get rid of annoying preferences*/
	remove(CUSTOM_USER_DIRECTORY PATHSEP "prefs.xml");
	remove(CUSTOM_USER_DIRECTORY PATHSEP "accounts.xml");
	remove(CUSTOM_USER_DIRECTORY PATHSEP "status.xml");
	remove(CUSTOM_USER_DIRECTORY PATHSEP "blist.xml");
	gboolean debug = atoi(argv[1]);
	GMainLoop *loop = g_main_loop_new(NULL, FALSE);
#ifndef WIN32
	signal(SIGCHLD, SIG_IGN);
	signal(SIGHUP, SIG_IGN);
//	signal(SIGPIPE, SIG_IGN);
#endif
	init_libpurple(debug);
	g_main_loop_run(loop);
	return 0;

}
