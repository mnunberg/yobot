/*
 * yobot_win32.c
 *
 *  Created on: Aug 22, 2010
 *      Author: mordy
 */


#include "yobot_log.h"
#include "win32/win32dep.h"
#include "fn_override.h"
#include <windows.h>
#include <winuser.h>
#include <glib.h>
#include <purple.h>

_declspec(dllexport) const char *new_wpurple_install_dir(void) {
	static char *install_dir = NULL;
	yobot_log_info("hi");
	if(!install_dir) {
		char *tmp = NULL;
		wchar_t _dir[MAXPATHLEN];
		/*get handle*/
		HMODULE purple_dll_handle = GetModuleHandle("libpurple.dll");
		if(!purple_dll_handle) {
			tmp = g_win32_error_message(GetLastError());
			purple_debug_error("wpurple", "GetModuleHandleW('libpurple.dll') error: %s", tmp);
			g_free(tmp);
			return NULL;
		}
		if (GetModuleFileNameW(purple_dll_handle, _dir, MAXPNAMELEN) > 0) {
			tmp = g_utf16_to_utf8(_dir, -1, NULL, NULL, NULL);
		}
		if(!tmp) {
			tmp = g_win32_error_message(GetLastError());
			purple_debug_error("wpurple", "GetModuleFileName('libpurple.dll') error: %s\n", tmp);
			g_free(tmp);
			return NULL;
		} else {
			install_dir = g_path_get_dirname(tmp);
			g_free(tmp);
		}
	}
	return install_dir;
}

void yobot_patch_purple_searchpath(void) {
	yobot_log_info("hacking wpurple_install_dir()");
	int status = 0;
	HMODULE purple = GetModuleHandle("libpurple.dll");
	if(!purple) {
		yobot_log_err("couldn't get libpurple handle: %s", g_win32_error_message(GetLastError()));
		return;
	}
	FARPROC srcptr = GetProcAddress(purple, "wpurple_install_dir");
	if(!srcptr) {
		yobot_log_err("couldn't get wpurple_install_dir address: %s", g_win32_error_message(GetLastError()));
		return;
	}
	FARPROC targetpr = GetProcAddress(GetModuleHandle(NULL), "new_wpurple_install_dir");
	if(!targetpr) {
		yobot_log_err("couldn't get target function address: %s", g_win32_error_message(GetLastError()));
		return;
	}
	status = yb_fn_override_by_ptr(srcptr, targetpr);
	if(!status) {
		yobot_log_err("couldn't override wpurple_install_dir");
	} else {
		yobot_log_info("done");
	}
}
