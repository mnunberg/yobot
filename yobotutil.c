/*
 * yobotutil.c
 *
 *  Created on: Aug 19, 2010
 *      Author: mordy
 */

#include <stdio.h>
#include <stdlib.h>
#include <glib.h>
#include <glib/gstdio.h>
#include "yobotutil.h"

/*This only removes actual files and symlinks in the tree. Does not follow symlinks*/
void yobot_rmdir_r(const gchar *startpath, gboolean keep_top) {
	if (g_file_test(startpath, G_FILE_TEST_IS_REGULAR|G_FILE_TEST_IS_SYMLINK)) {
		if (!keep_top) {
			printf("Would delete: %s\n", startpath);
			g_unlink(startpath);
		}
	} else /*is a directory*/ {
		GError *error = NULL;
		GDir *dir = g_dir_open(startpath, 0, &error);
		if(dir) {
			const gchar *entry;
			while((entry = g_dir_read_name(dir))) {
				char *tmp = g_build_path(G_DIR_SEPARATOR_S, startpath, entry, NULL);
				yobot_rmdir_r(tmp, FALSE);
				g_free(tmp);
			}
			g_dir_close(dir);
		}
	}
}
