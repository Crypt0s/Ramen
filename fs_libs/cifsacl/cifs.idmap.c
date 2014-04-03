/*
* CIFS idmap helper.
* Copyright (C) Shirish Pargaonkar (shirishp@us.ibm.com) 2011
*
* Used by /sbin/request-key.conf for handling
* cifs upcall for SID to uig/gid and uid/gid to SID mapping.
* You should have keyutils installed and add
* this lines to /etc/request-key.conf file:

    create cifs.idmap * * /usr/local/sbin/cifs.idmap %k

* This program is free software; you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation; either version 2 of the License, or
* (at your option) any later version.
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
* GNU General Public License for more details.
* You should have received a copy of the GNU General Public License
* along with this program; if not, write to the Free Software
* Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
*/

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif /* HAVE_CONFIG_H */

#include <string.h>
#include <getopt.h>
#include <syslog.h>
#include <dirent.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <keyutils.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <limits.h>
#include <wbclient.h>

static const char *prog = "cifs.idmap";

static void usage(void)
{
	fprintf(stderr, "Usage: %s key_serial\n", prog);
}

char *strget(const char *str, char *substr)
{
	int len, sublen, retlen;
	char *retstr, *substrptr;

	sublen = strlen(substr);
	substrptr = strstr(str, substr);
	if (substrptr) {
		len = strlen(substrptr);
		substrptr += sublen;

		retlen = len - sublen;
		if (retlen > 0) {
			retstr = malloc(retlen + 1);
			if (retstr) {
				strncpy(retstr, substrptr, retlen);
				return retstr;
			}
		}
	}

	return NULL;
}

static int
cifs_idmap(const key_serial_t key, const char *key_descr)
{
	uid_t uid = 0;
	gid_t gid = 0;;
	wbcErr rc = 1;
	char *sidstr = NULL;
	struct wbcDomainSid sid;

	/*
	 * Use winbind to convert received string to a SID and lookup
	 * name and map that SID to an uid.  If either of these
	 * function calls return with an error, return an error the
	 * upcall caller.  Otherwise instanticate a key using that uid.
	 *
	 * The same applies to SID and gid mapping.
	 */
	sidstr = strget(key_descr, "os:");
	if (sidstr) {
		rc = wbcStringToSid(sidstr, &sid);
		if (rc)
			syslog(LOG_DEBUG, "Invalid owner string: %s, rc: %d",
				key_descr, rc);
		else {
			rc = wbcSidToUid(&sid, &uid);
			if (rc)
				syslog(LOG_DEBUG, "SID %s to uid wbc error: %d",
						key_descr, rc);
		}
		if (!rc) { /* SID has been mapped to an uid */
			rc = keyctl_instantiate(key, &uid, sizeof(uid_t), 0);
			if (rc)
				syslog(LOG_ERR, "%s: key inst: %s",
					__func__, strerror(errno));
		}

		goto cifs_idmap_ret;
	}

	sidstr = strget(key_descr, "gs:");
	if (sidstr) {
		rc = wbcStringToSid(sidstr, &sid);
		if (rc)
			syslog(LOG_DEBUG, "Invalid group string: %s, rc: %d",
					key_descr, rc);
		else {
			rc = wbcSidToGid(&sid, &gid);
			if (rc)
				syslog(LOG_DEBUG, "SID %s to gid wbc error: %d",
						key_descr, rc);
		}
		if (!rc) { /* SID has been mapped to a gid */
			rc = keyctl_instantiate(key, &gid, sizeof(gid_t), 0);
			if (rc)
				syslog(LOG_ERR, "%s: key inst: %s",
						__func__, strerror(errno));
		}

		goto cifs_idmap_ret;
	}

	sidstr = strget(key_descr, "oi:");
	if (sidstr) {
		uid = atoi(sidstr);
		syslog(LOG_DEBUG, "SID: %s, uid: %d", sidstr, uid);
		rc = wbcUidToSid(uid, &sid);
		if (rc)
			syslog(LOG_DEBUG, "uid %d to SID  error: %d", uid, rc);
		if (!rc) { /* SID has been mapped to a uid */
			rc = keyctl_instantiate(key, &sid,
					sizeof(struct wbcDomainSid), 0);
			if (rc)
				syslog(LOG_ERR, "%s: key inst: %s",
					__func__, strerror(errno));
		}

		goto cifs_idmap_ret;
	}

	sidstr = strget(key_descr, "gi:");
	if (sidstr) {
		gid = atoi(sidstr);
		syslog(LOG_DEBUG, "SID: %s, gid: %d", sidstr, gid);
		rc = wbcGidToSid(gid, &sid);
		if (rc)
			syslog(LOG_DEBUG, "gid %d to SID error: %d", gid, rc);
		if (!rc) { /* SID has been mapped to a gid */
			rc = keyctl_instantiate(key, &sid,
					sizeof(struct wbcDomainSid), 0);
			if (rc)
				syslog(LOG_ERR, "%s: key inst: %s",
					__func__, strerror(errno));
		}

		goto cifs_idmap_ret;
	}


	syslog(LOG_DEBUG, "Invalid key: %s", key_descr);

cifs_idmap_ret:
	if (sidstr)
		free(sidstr);

	return rc;
}

int main(const int argc, char *const argv[])
{
	int c;
	long rc = 1;
	key_serial_t key = 0;
	char *buf;

	openlog(prog, 0, LOG_DAEMON);

	while ((c = getopt_long(argc, argv, "v", NULL, NULL)) != -1) {
		switch (c) {
		case 'v':
			printf("version: %s\n", VERSION);
			goto out;
		default:
			syslog(LOG_ERR, "unknown option: %c", c);
			goto out;
		}
	}

	/* is there a key? */
	if (argc <= optind) {
		usage();
		goto out;
	}

	/* get key and keyring values */
	errno = 0;
	key = strtol(argv[optind], NULL, 10);
	if (errno != 0) {
		key = 0;
		syslog(LOG_ERR, "Invalid key format: %s", strerror(errno));
		goto out;
	}

	rc = keyctl_describe_alloc(key, &buf);
	if (rc == -1) {
		syslog(LOG_ERR, "keyctl_describe_alloc failed: %s",
		       strerror(errno));
		rc = 1;
		goto out;
	}

	syslog(LOG_DEBUG, "key description: %s", buf);

	if ((strncmp(buf, "cifs.idmap", sizeof("cifs.idmap") - 1) == 0))
		rc = cifs_idmap(key, buf);
out:
	return rc;
}
