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
#include "yobotutil.h"
#include <errno.h>
#include <stdbool.h>
#include <string.h>

#ifdef _WIN32
#include "win32/win32dep.h"
#include <windows.h>
#define CUSTOM_USER_DIRECTORY  "C:" G_DIR_SEPARATOR_S "temp" G_DIR_SEPARATOR_S "yobot"
#define WPURPLE_ROOT "C:\\Program Files\\Pidgin"
#else
#define CUSTOM_USER_DIRECTORY G_DIR_SEPARATOR_S "tmp" G_DIR_SEPARATOR_S "yobot"
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
	PurpleAccount *account;
} PurpleGLibIOClosure;

typedef struct {
	GSourceFunc function;
	guint result;
	gpointer data;
	PurpleAccount *account;
} YobotPurpleTimeoutCb;

static void purple_glib_io_destroy(gpointer data)
{
	g_free(data);
}

PurpleAccount *global_current_account = NULL;

static gboolean purple_glib_io_invoke(GIOChannel *source, GIOCondition condition, gpointer data)
{
	PurpleGLibIOClosure *closure = data;
	PurpleInputCondition purple_cond = 0;
	yobot_purple_account_context_set(closure->account);
	yobot_purple_account_context_printf();

	if (condition & PURPLE_GLIB_READ_COND)
		purple_cond |= PURPLE_INPUT_READ;
	if (condition & PURPLE_GLIB_WRITE_COND)
		purple_cond |= PURPLE_INPUT_WRITE;
	int fd = g_io_channel_unix_get_fd(source);
	closure->function(closure->data, fd, purple_cond);
	return TRUE;
}

static guint glib_input_add(gint fd, PurpleInputCondition condition, PurpleInputFunction function,
		gpointer data) {
	PurpleGLibIOClosure *closure = g_new0(PurpleGLibIOClosure, 1);
	GIOChannel *channel;
	GIOCondition cond = 0;

	closure->function = function;
	closure->data = data;
	closure->account = yobot_purple_account_context_get();

	if (condition & PURPLE_INPUT_READ)
		cond |= PURPLE_GLIB_READ_COND;
	if (condition & PURPLE_INPUT_WRITE)
		cond |= PURPLE_GLIB_WRITE_COND;

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

static void glib_timeout_destroy(gpointer data) {
	g_free(data);
}

static gboolean glib_timeout_invoke(gpointer data) {
	YobotPurpleTimeoutCb *cbinfo = data;
	/*set context*/
	yobot_purple_account_context_set(cbinfo->account);
	yobot_purple_account_context_printf();
	return cbinfo->function(cbinfo->data);
}

static guint glib_timeout_add(guint interval, GSourceFunc function, gpointer data) {
	YobotPurpleTimeoutCb *cbinfo = g_new0(YobotPurpleTimeoutCb, 1);
	cbinfo->data = data;
	cbinfo->function = function;
	cbinfo->account = yobot_purple_account_context_get();
	cbinfo->result = g_timeout_add_full(G_PRIORITY_DEFAULT, interval,
			glib_timeout_invoke, cbinfo, glib_timeout_destroy);
	return cbinfo->result;
}

static PurpleEventLoopUiOps glib_eventloops =
{
	glib_timeout_add,
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


static void init_libpurple(int debug, char *directory)
{
	/*mandatory.. so it doesn't mess with whatever. Keep blist.xml so we have cached
	 * icons. For some reason problems only occur on windows*/
	char *remove_list[] = {"prefs.xml", "accounts.xml", "xmpp-caps.xml", NULL};
	int i = 0;
	while (remove_list[i]) {
		char *tmp = g_build_path(G_DIR_SEPARATOR_S, directory, remove_list[i], NULL);
		if(remove(tmp) == -1) {
			yobot_log_warn("Error cleaning %s: %s", tmp, strerror(errno));
		}
		g_free(tmp);
		i++;
	}
	purple_util_set_user_dir(directory);
	purple_debug_set_enabled(debug);

	purple_core_set_ui_ops(&core_uiops);
	purple_debug_set_ui_ops(&yobot_libpurple_debug_uiops);
	purple_eventloop_set_ui_ops(&glib_eventloops);

	if (!purple_core_init(UI_ID)) {
		fprintf(stderr,
				"libpurple initialization failed. Dumping core.\n"
				"Please report this!\n");
		abort();
	}
	purple_set_blist(purple_blist_new());
	purple_blist_load();
	purple_prefs_load();
	/*some settings for our application*/
	purple_prefs_set_bool("/purple/away/away_when_idle", false);
	purple_prefs_set_string("/purple/away/idle_reporting", "system");
	/*logging...*/
	purple_prefs_set_bool("/purple/logging/log_ims", false);
	purple_prefs_set_bool("/purple/logging/log_chats", false);
	purple_prefs_set_bool("/purple/logging/log_system", false);

}


yobot_log_s yobot_log_params = {
		"Yobot-Purple",
		1
};


int yobot_application_mode = YOBOT_DESKTOP;
char *yobot_listen_address = NULL;
char *yobot_listen_port = NULL;

int main(int argc, char *argv[])
{
	/*set up option parsing...*/
	int debug = 0;
	char *config_dir = NULL;
	char *mode = NULL;
	char *addrport = NULL;
	gboolean clean_confdir = FALSE;
	GError *error = NULL;

	GOptionEntry entries[] =
	{
			{ "debug", 'd', 0, G_OPTION_ARG_INT, &debug, "0 turns off debugging, anthing else turns it on", "LEVEL" },
			{ "config-dir", 'c' , 0, G_OPTION_ARG_STRING, &config_dir, "Configuration directory, defaults to $HOME/.yobot/purple", "DIR" },
			{ "mode", 'm', 0, G_OPTION_ARG_STRING, &mode, "Mode, 'desktop' or 'daemon'", "MODE"},
			{ "clean", 0, 0, G_OPTION_ARG_NONE, &clean_confdir, "Clean configuration directory. Useful for debugging"},
			{ "listening-address", 'l', 0, G_OPTION_ARG_STRING, &addrport, "Listening address in the form of address:port"},
			{NULL}
	};
	GOptionContext *context = g_option_context_new("Yobot purple command server");
	g_option_context_add_main_entries(context, entries, NULL);
	if(!g_option_context_parse(context, &argc, &argv, &error)) {
		g_print("option parsing failed: %s\n", error->message);
		exit(1);
	}

	if (mode && strcmp(mode, "daemon")==0)
		yobot_application_mode = YOBOT_DAEMON;

	/*build configuration directory path*/
	if (!config_dir) {
		/*configuration directory was not specified on the command line*/
		if(!(config_dir = getenv("YOBOT_USER_DIR"))) {
			config_dir = g_build_path(G_DIR_SEPARATOR_S, g_get_home_dir(), ".yobot", "purple", NULL);
		} else {
			config_dir = g_build_path(G_DIR_SEPARATOR_S, config_dir, "purple", NULL);
		}
	} else {
		config_dir = g_build_path(G_DIR_SEPARATOR_S, config_dir, "purple", NULL);
	}

	/*make the directory...*/
	if (g_mkdir_with_parents(config_dir, 0700)<0) {
		yobot_log_warn("Couldn't mkdir %s: %s", config_dir, strerror(errno));
		g_free(config_dir);
		config_dir = g_build_path(G_DIR_SEPARATOR_S, g_get_tmp_dir(), "yobot_failover", g_get_user_name(), "purple", NULL);
		yobot_log_warn("trying failover path of %s", config_dir);
		if (g_mkdir_with_parents(config_dir, 0700)<0) {
			yobot_log_crit("failed to make failover directory %s: %s. Aborting!", config_dir, strerror(errno));
			exit(EXIT_FAILURE);
		}
	}
	if (clean_confdir) {
		yobot_log_warn("emptying configuration directory %s", config_dir);
		yobot_rmdir_r(config_dir, TRUE);
	}
	if (addrport) {
		char **tmp = g_strsplit(addrport, ":", 2);
		if(tmp[0] && tmp[1]) {
			yobot_listen_address = tmp[0];
			yobot_listen_port = tmp[1];
		} else {
			yobot_log_err("got bad address value: '%s'", addrport);
			exit(EXIT_FAILURE);
		}
	} else {
		yobot_listen_address = "localhost";
		yobot_listen_port = "7771";
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
	GMainLoop *loop = g_main_loop_new(NULL, FALSE);
#ifndef WIN32
	signal(SIGCHLD, SIG_IGN);
	signal(SIGHUP, SIG_IGN);
#endif
	init_libpurple(debug, config_dir);
	g_main_loop_run(loop);
	return 0;

}
