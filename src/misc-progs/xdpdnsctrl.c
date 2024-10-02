/* This file is part of the BPFire Firewall.
 *
 * This program is distributed under the terms of the GNU General Public
 * Licence.  See the file COPYING for details.
 *
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <fcntl.h>
#include "setuid.h"

int main(int argc, char *argv[]) {

	if (!(initsetuid()))
		exit(1);

	if (argc < 2) {
		fprintf(stderr, "\nNo argument given.\n\nddosctrl (start|stop|restart)\n\n");
		exit(1);
	}

	if (strcmp(argv[1], "start") == 0) {
		safe_system("/etc/rc.d/init.d/xdpdns start");
	} else if (strcmp(argv[1], "stop") == 0) {
		safe_system("/etc/rc.d/init.d/xdpdns stop");
	} else if (strcmp(argv[1], "restart") == 0) {
		safe_system("/etc/rc.d/init.d/xdpdns restart");
	} else if (strcmp(argv[1], "status") == 0) {
		safe_system("/etc/rc.d/init.d/xdpdns status");
	} else {
		fprintf(stderr, "\nBad argument given.\n\nxdpdnsctrl (start|stop|restart|status)\n\n");
		exit(1);
	}

	return 0;
}
