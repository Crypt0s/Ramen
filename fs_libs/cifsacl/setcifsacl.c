/*
* setcifsacl utility
*
* Copyright (C) Shirish Pargaonkar (shirishp@us.ibm.com) 2011
*
* Used to alter entries of an ACL or replace an entire ACL in a
* security descriptor of a file system object that belongs to a
* share mounted using option cifsacl.
*
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
#include <stdint.h>
#include <stdbool.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <limits.h>
#include <wbclient.h>
#include <ctype.h>
#include <sys/xattr.h>
#include "cifsacl.h"

static const char *prog = "setcifsacl";

static void
copy_sec_desc(const struct cifs_ntsd *pntsd, struct cifs_ntsd *pnntsd,
		int numaces, int acessize)
{
	int i;

	int osidsoffset, gsidsoffset, dacloffset;
	struct cifs_sid *owner_sid_ptr, *group_sid_ptr;
	struct cifs_sid *nowner_sid_ptr, *ngroup_sid_ptr;
	struct cifs_ctrl_acl *dacl_ptr, *ndacl_ptr;

	/* copy security descriptor control portion */
	osidsoffset = htole32(pntsd->osidoffset);
	gsidsoffset = htole32(pntsd->gsidoffset);
	dacloffset = htole32(pntsd->dacloffset);

	pnntsd->revision = pntsd->revision;
	pnntsd->type = pntsd->type;
	pnntsd->osidoffset = pntsd->osidoffset;
	pnntsd->gsidoffset = pntsd->gsidoffset;
	pnntsd->dacloffset = pntsd->dacloffset;

	dacl_ptr = (struct cifs_ctrl_acl *)((char *)pntsd + dacloffset);
	ndacl_ptr = (struct cifs_ctrl_acl *)((char *)pnntsd + dacloffset);

	ndacl_ptr->revision = dacl_ptr->revision;
	ndacl_ptr->size = htole16(acessize + sizeof(struct cifs_ctrl_acl));
	ndacl_ptr->num_aces = htole32(numaces);

	/* copy owner sid */
	owner_sid_ptr = (struct cifs_sid *)((char *)pntsd + osidsoffset);
	nowner_sid_ptr = (struct cifs_sid *)((char *)pnntsd + osidsoffset);

	nowner_sid_ptr->revision = owner_sid_ptr->revision;
	nowner_sid_ptr->num_subauth = owner_sid_ptr->num_subauth;
	for (i = 0; i < 6; i++)
		nowner_sid_ptr->authority[i] = owner_sid_ptr->authority[i];
	for (i = 0; i < 5; i++)
		nowner_sid_ptr->sub_auth[i] = owner_sid_ptr->sub_auth[i];

	/* copy group sid */
	group_sid_ptr = (struct cifs_sid *)((char *)pntsd + gsidsoffset);
	ngroup_sid_ptr = (struct cifs_sid *)((char *)pnntsd + gsidsoffset);

	ngroup_sid_ptr->revision = group_sid_ptr->revision;
	ngroup_sid_ptr->num_subauth = group_sid_ptr->num_subauth;
	for (i = 0; i < 6; i++)
		ngroup_sid_ptr->authority[i] = group_sid_ptr->authority[i];
	for (i = 0; i < 5; i++)
		ngroup_sid_ptr->sub_auth[i] = group_sid_ptr->sub_auth[i];

	return;
}

static int
copy_ace(struct cifs_ace *dace, struct cifs_ace *sace)
{
	int i;

	dace->type = sace->type;
	dace->flags = sace->flags;
	dace->access_req = htole32(sace->access_req);

	dace->sid.revision = sace->sid.revision;
	dace->sid.num_subauth = sace->sid.num_subauth;
	for (i = 0; i < 6; i++)
		dace->sid.authority[i] = sace->sid.authority[i];
	for (i = 0; i < sace->sid.num_subauth; i++)
		dace->sid.sub_auth[i] = sace->sid.sub_auth[i];

	dace->size = htole16(sace->size);

	return dace->size;
}

static int
compare_aces(struct cifs_ace *sace, struct cifs_ace *dace, int compflags)
{
	int i;

	if (compflags & COMPSID) {
		if (dace->sid.revision != sace->sid.revision)
			return 0;
		if (dace->sid.num_subauth != sace->sid.num_subauth)
			return 0;
		for (i = 0; i < 6; i++) {
			if (dace->sid.authority[i] != sace->sid.authority[i])
				return 0;
		}
		for (i = 0; i < sace->sid.num_subauth; i++) {
			if (dace->sid.sub_auth[i] != sace->sid.sub_auth[i])
				return 0;
		}
	}

	if (compflags & COMPTYPE) {
		if (dace->type != sace->type)
			return 0;
	}

	if (compflags & COMPFLAG) {
		if (dace->flags != sace->flags)
			return 0;
	}

	if (compflags & COMPMASK) {
		if (dace->access_req != htole32(sace->access_req))
			return 0;
	}

	return 1;
}

static int
get_sec_desc_size(struct cifs_ntsd *pntsd, struct cifs_ntsd **npntsd,
			int aces, ssize_t *bufsize, size_t *acesoffset)
{
	unsigned int size, acessize, dacloffset;

	size = sizeof(struct cifs_ntsd) +
		2 * sizeof(struct cifs_sid) +
		sizeof(struct cifs_ctrl_acl);

	dacloffset = le32toh(pntsd->dacloffset);

	*acesoffset = dacloffset + sizeof(struct cifs_ctrl_acl);
	acessize = aces * sizeof(struct cifs_ace);
	*bufsize = size + acessize;

	*npntsd = malloc(*bufsize);
	if (!*npntsd) {
		printf("%s: Memory allocation failure", __func__);
		return errno;
	}

	return 0;
}

static int
ace_set(struct cifs_ntsd *pntsd, struct cifs_ntsd **npntsd, ssize_t *bufsize,
			struct cifs_ace **cacesptr, int numcaces)
{
	int i, rc, acessize = 0;
	size_t acesoffset;
	char *acesptr;

	rc = get_sec_desc_size(pntsd, npntsd, numcaces, bufsize, &acesoffset);
	if (rc)
		return rc;

	acesptr = (char *)*npntsd + acesoffset;
	for (i = 0; i < numcaces; ++i) {
		acessize += copy_ace((struct cifs_ace *)acesptr, cacesptr[i]);
		acesptr += sizeof(struct cifs_ace);
	}
	copy_sec_desc(pntsd, *npntsd, numcaces, acessize);
	acesptr = (char *)*npntsd + acesoffset;


	return 0;
}

static int
ace_add(struct cifs_ntsd *pntsd, struct cifs_ntsd **npntsd, ssize_t *bufsize,
		struct cifs_ace **facesptr, int numfaces,
		struct cifs_ace **cacesptr, int numcaces)
{
	int i, rc, numaces, size, acessize = 0;
	size_t acesoffset;
	char *acesptr;

	numaces = numfaces + numcaces;
	rc = get_sec_desc_size(pntsd, npntsd, numaces, bufsize, &acesoffset);
	if (rc)
		return rc;

	acesptr = (char *)*npntsd + acesoffset;
	for (i = 0; i < numfaces; ++i) {
		size = copy_ace((struct cifs_ace *)acesptr, facesptr[i]);
		acesptr += size;
		acessize += size;
	}
	for (i = 0; i < numcaces; ++i) {
		size = copy_ace((struct cifs_ace *)acesptr, cacesptr[i]);
		acesptr += size;
		acessize += size;
	}
	copy_sec_desc(pntsd, *npntsd, numaces, acessize);

	return 0;
}

static int
ace_modify(struct cifs_ntsd *pntsd, struct cifs_ntsd **npntsd, ssize_t *bufsize,
		struct cifs_ace **facesptr, int numfaces,
		struct cifs_ace **cacesptr, int numcaces)
{
	int i, j, rc, size, acessize = 0;
	size_t acesoffset;
	char *acesptr;

	if (numfaces == 0) {
		printf("%s: No entries to modify", __func__);
		return -1;
	}

	rc = get_sec_desc_size(pntsd, npntsd, numfaces, bufsize, &acesoffset);
	if (rc)
		return rc;

	for (j = 0; j < numcaces; ++j) {
		for (i = 0; i < numfaces; ++i) {
			if (compare_aces(facesptr[i], cacesptr[j],
					COMPSID | COMPTYPE)) {
				copy_ace(facesptr[i], cacesptr[j]);
				break;
			}
		}
	}

	acesptr = (char *)*npntsd + acesoffset;
	for (i = 0; i < numfaces; ++i) {
		size = copy_ace((struct cifs_ace *)acesptr, facesptr[i]);
		acesptr += size;
		acessize += size;
	}

	copy_sec_desc(pntsd, *npntsd, numfaces, acessize);

	return 0;
}

static int
ace_delete(struct cifs_ntsd *pntsd, struct cifs_ntsd **npntsd, ssize_t *bufsize,
		struct cifs_ace **facesptr, int numfaces,
		struct cifs_ace **cacesptr, int numcaces)
{
	int i, j, numaces = 0, rc, size, acessize = 0;
	size_t acesoffset;
	char *acesptr;

	if (numfaces == 0) {
		printf("%s: No entries to delete\n", __func__);
		return -1;
	}

	if (numfaces < numcaces) {
		printf("%s: Invalid entries to delete\n", __func__);
		return -1;
	}

	rc = get_sec_desc_size(pntsd, npntsd, numfaces, bufsize, &acesoffset);
	if (rc)
		return rc;

	acesptr = (char *)*npntsd + acesoffset;
	for (i = 0; i < numfaces; ++i) {
		for (j = 0; j < numcaces; ++j) {
			if (compare_aces(facesptr[i], cacesptr[j], COMPALL))
				break;
		}
		if (j == numcaces) {
			size = copy_ace((struct cifs_ace *)acesptr,
								facesptr[i]);
			acessize += size;
			acesptr += size;
			++numaces;
		}
	}

	if (numaces == numfaces) {
		printf("%s: Nothing to delete\n", __func__);
		return 1;
	}
	copy_sec_desc(pntsd, *npntsd, numaces, acessize);

	return 0;
}

static int
get_numfaces(struct cifs_ntsd *pntsd, ssize_t acl_len,
			struct cifs_ctrl_acl **daclptr)
{
	int numfaces = 0;
	uint32_t dacloffset;
	struct cifs_ctrl_acl *ldaclptr;
	char *end_of_acl = ((char *)pntsd) + acl_len;

	if (pntsd == NULL)
		return 0;

	dacloffset = le32toh(pntsd->dacloffset);
	if (!dacloffset)
		return 0;
	else {
		ldaclptr = (struct cifs_ctrl_acl *)((char *)pntsd + dacloffset);
		/* validate that we do not go past end of acl */
		if (end_of_acl >= (char *)ldaclptr + le16toh(ldaclptr->size)) {
			numfaces = le32toh(ldaclptr->num_aces);
			*daclptr = ldaclptr;
		}
	}

	return numfaces;
}

static struct cifs_ace **
build_fetched_aces(char *daclptr, int numfaces)
{
	int i, j, rc = 0, acl_size;
	char *acl_base;
	struct cifs_ace *pace, **facesptr;

	facesptr = (struct cifs_ace **)malloc(numfaces *
					sizeof(struct cifs_aces *));
	if (!facesptr) {
		printf("%s: Error %d allocating ACE array",
				__func__, errno);
		rc = errno;
	}

	acl_base = daclptr;
	acl_size = sizeof(struct cifs_ctrl_acl);
	for (i = 0; i < numfaces; ++i) {
		facesptr[i] = malloc(sizeof(struct cifs_ace));
		if (!facesptr[i]) {
			rc = errno;
			goto build_fetched_aces_ret;
		}
		pace = (struct cifs_ace *) (acl_base + acl_size);
		memcpy(facesptr[i], pace, sizeof(struct cifs_ace));
		acl_base = (char *)pace;
		acl_size = le16toh(pace->size);
	}

build_fetched_aces_ret:
	if (rc) {
		printf("%s: Invalid fetched ace\n", __func__);
		if (i) {
			for (j = i; j >= 0; --j)
				free(facesptr[j]);
		}
		free(facesptr);
	}
	return facesptr;
}

static int
verify_ace_sid(char *sidstr, struct cifs_sid *sid)
{
	int rc;
	char *lstr;
	struct passwd *winpswdptr;

	lstr = strstr(sidstr, "\\"); /* everything before | */
	if (lstr)
		++lstr;
	else
		lstr = sidstr;

	/* Check if it is a (raw) SID (string) */
	rc = wbcStringToSid(lstr, (struct wbcDomainSid *)sid);
	if (!rc)
		return rc;

	/* Check if it a name (string) which can be resolved to a SID*/
	rc = wbcGetpwnam(lstr, &winpswdptr);
	if (rc) {
		printf("%s: Invalid user name: %s\n", __func__, sidstr);
		return rc;
	}
	rc = wbcUidToSid(winpswdptr->pw_uid, (struct wbcDomainSid *)sid);
	if (rc) {
		printf("%s: Invalid user: %s\n", __func__, sidstr);
		return rc;
	}

	return 0;
}

static int
verify_ace_type(char *typestr, uint8_t *typeval)
{
	int i, len;
	char *invaltype;

	if (strstr(typestr, "0x")) { /* hex type value */
		*typeval = strtol(typestr, &invaltype, 16);
		if (!strlen(invaltype)) {
			if (*typeval != ACCESS_ALLOWED &&
				*typeval != ACCESS_DENIED &&
				*typeval != ACCESS_ALLOWED_OBJECT &&
				*typeval != ACCESS_DENIED_OBJECT) {
					printf("%s: Invalid type: %s\n",
						__func__, typestr);
					return 1;
			}
			return 0;
		}
	}

	len = strlen(typestr);
	for (i = 0; i < len; ++i)
		*(typestr + i) = toupper(*(typestr + i));
	if (!strcmp(typestr, "ALLOWED"))
		*typeval = 0x0;
	else if (!strcmp(typestr, "DENIED"))
		*typeval = 0x1;
	else if (!strcmp(typestr, "ALLOWED_OBJECT"))
		*typeval = 0x5;
	else if (!strcmp(typestr, "DENIED_OBJECT"))
		*typeval = 0x6;
	else {
		printf("%s: Invalid type: %s\n", __func__, typestr);
		return 1;
	}

	return 0;
}

static uint8_t
ace_flag_value(char *flagstr)
{
	uint8_t flagval = 0x0;
	char *iflag;

	iflag = strtok(flagstr, "|"); /* everything before | */
	while (iflag) {
		if (!strcmp(iflag, "OI"))
			flagval += 0x1;
		else if (!strcmp(iflag, "CI"))
			flagval += 0x2;
		else if (!strcmp(iflag, "NP"))
			flagval += 0x4;
		else if (!strcmp(iflag, "IO"))
			flagval += 0x8;
		else if (!strcmp(iflag, "I"))
			flagval += 0x10;
		else
			return 0x0; /* Invalid flag */
		iflag = strtok(NULL, "|"); /* everything before | */
	}

	return flagval;
}

static int
verify_ace_flags(char *flagstr, uint8_t *flagval)
{
	char *invalflag;

	if (!strcmp(flagstr, "0") || !strcmp(flagstr, "0x0"))
		return 0;

	if (strstr(flagstr, "0x")) { /* hex flag value */
		*flagval = strtol(flagstr, &invalflag, 16);
		if (strlen(invalflag)) {
			printf("%s: Invalid flags: %s\n", __func__, flagstr);
			return 1;
		}
	} else
		*flagval = ace_flag_value(flagstr);

	if (!*flagval || (*flagval & ~VFLAGS)) {
		printf("%s: Invalid flag %s and value: 0x%x\n",
			__func__, flagstr, *flagval);
		return 1;
	}

	return 0;
}

static uint32_t
ace_mask_value(char *maskstr)
{
	int i, len;
	uint32_t maskval = 0x0;
	char *lmask;

	if (!strcmp(maskstr, "FULL"))
		return FULL_CONTROL;
	else if (!strcmp(maskstr, "CHANGE"))
		return CHANGE;
	else if (!strcmp(maskstr, "D"))
		return DELETE;
	else if (!strcmp(maskstr, "READ"))
		return EREAD;
	else {
		len = strlen(maskstr);
		lmask = maskstr;
		for (i = 0; i < len; ++i, ++lmask) {
			if (*lmask == 'R')
				maskval |= EREAD;
			else if (*lmask == 'W')
				maskval |= EWRITE;
			else if (*lmask == 'X')
				maskval |= EXEC;
			else if (*lmask == 'D')
				maskval |= DELETE;
			else if (*lmask == 'P')
				maskval |= WRITE_DAC;
			else if (*lmask == 'O')
				maskval |= WRITE_OWNER;
			else
				return 0;
		}
		return maskval;
	}

	return 0;
}

static int
verify_ace_mask(char *maskstr, uint32_t *maskval)
{
	char *invalflag;

	if (strstr(maskstr, "0x") || !strcmp(maskstr, "DELDHLD")) {
		*maskval = strtol(maskstr, &invalflag, 16);
		if (!invalflag) {
			printf("%s: Invalid mask: %s\n", __func__, maskstr);
			return 1;
		}
	} else
		*maskval = ace_mask_value(maskstr);

	if (!*maskval) {
		printf("%s: Invalid mask %s and value: 0x%x\n",
			__func__, maskstr, *maskval);
		return 1;
	}

	return 0;
}

static struct cifs_ace **
build_cmdline_aces(char **arrptr, int numcaces)
{
	int i;
	char *acesid, *acetype, *aceflag, *acemask;
	struct cifs_ace **cacesptr;

	cacesptr = (struct cifs_ace **)malloc(numcaces *
				sizeof(struct cifs_aces *));
	if (!cacesptr) {
		printf("%s: Error %d allocating ACE array", __func__, errno);
		return NULL;
	}

	for (i = 0; i < numcaces; ++i) {
		acesid = strtok(arrptr[i], ":");
		acetype = strtok(NULL, "/");
		aceflag = strtok(NULL, "/");
		acemask = strtok(NULL, "/");

		if (!acesid || !acetype || !aceflag || !acemask) {
			printf("%s: Incomplete ACE: %s\n", __func__, arrptr[i]);
			goto build_cmdline_aces_ret;
		}

		cacesptr[i] = malloc(sizeof(struct cifs_ace));
		if (!cacesptr[i]) {
			printf("%s: ACE alloc error %d\n", __func__, errno);
			goto build_cmdline_aces_ret;
		}

		if (verify_ace_sid(acesid, &cacesptr[i]->sid)) {
			printf("%s: Invalid SID: %s\n", __func__, arrptr[i]);
			goto build_cmdline_aces_ret;
		}

		if (verify_ace_type(acetype, &cacesptr[i]->type)) {
			printf("%s: Invalid ACE type: %s\n",
					__func__, arrptr[i]);
			goto build_cmdline_aces_ret;
		}

		if (verify_ace_flags(aceflag, &cacesptr[i]->flags)) {
			printf("%s: Invalid ACE flag: %s\n",
				__func__, arrptr[i]);
			goto build_cmdline_aces_ret;
		}

		if (verify_ace_mask(acemask, &cacesptr[i]->access_req)) {
			printf("%s: Invalid ACE mask: %s\n",
				__func__, arrptr[i]);
			goto build_cmdline_aces_ret;
		}

		cacesptr[i]->size = 1 + 1 + 2 + 4 + 1 + 1 + 6 +
				(cacesptr[i]->sid.num_subauth * 4);
	}
	return cacesptr;

build_cmdline_aces_ret:
	for (; i >= 0; --i)
		free(cacesptr[i]);
	free(cacesptr);
	return NULL;
}

static char **
parse_cmdline_aces(char *optarg, int numcaces)
{
	int i = 0, len;
	char *acestr, *vacestr, **arrptr = NULL;

	errno = EINVAL;
	arrptr = (char **)malloc(numcaces * sizeof(char *));
	if (!arrptr) {
		printf("%s: Error %d allocating char array\n", __func__, errno);
		return NULL;
	}

	while (i < numcaces) {
		acestr = strtok(optarg, ","); /* everything before , */
		if (acestr) {
			vacestr = strstr(acestr, "ACL:"); /* ace as ACL:*" */
			if (vacestr) {
				vacestr = strchr(vacestr, ':');
				if (vacestr)
					++vacestr; /* go past : */
				if (vacestr) {
					len = strlen(vacestr);
					arrptr[i] = malloc(len + 1);
					if (!arrptr[i])
						goto parse_cmdline_aces_ret;
					strcpy(arrptr[i], vacestr);
					++i;
				} else
					goto parse_cmdline_aces_ret;
			} else
				goto parse_cmdline_aces_ret;
		} else
			goto parse_cmdline_aces_ret;
		optarg = NULL;
	}
	errno = 0;
	return arrptr;

parse_cmdline_aces_ret:
	printf("%s: Error %d parsing ACEs\n", __func__, errno);
	for (;  i >= 0; --i)
		free(arrptr[i]);
	free(arrptr);
	return NULL;
}

static unsigned int
get_numcaces(const char *optarg)
{
	int i, len;
	unsigned int numcaces = 1;

	if (!optarg)
		return 0;

	len = strlen(optarg);
	for (i = 0; i < len; ++i) {
		if (*(optarg + i) == ',')
			++numcaces;
	}

	return numcaces;
}

static int
setacl_action(struct cifs_ntsd *pntsd, struct cifs_ntsd **npntsd,
		ssize_t *bufsize, struct cifs_ace **facesptr, int numfaces,
		struct cifs_ace **cacesptr, int numcaces,
		int maction)
{
	int rc = 1;

	switch (maction) {
	case 0:
		rc = ace_delete(pntsd, npntsd, bufsize, facesptr,
				numfaces, cacesptr, numcaces);
		break;
	case 1:
		rc = ace_modify(pntsd, npntsd, bufsize, facesptr,
				numfaces, cacesptr, numcaces);
		break;
	case 2:
		rc = ace_add(pntsd, npntsd, bufsize, facesptr,
				numfaces, cacesptr, numcaces);
		break;
	case 3:
		rc = ace_set(pntsd, npntsd, bufsize, cacesptr, numcaces);
		break;
	default:
		printf("%s: Invalid action: %d\n", __func__, maction);
		break;
	}

	return rc;
}

static void
setcifsacl_usage(void)
{
	fprintf(stderr,
	"%s: Alter CIFS/NTFS ACL in a security descriptor of a file object\n",
		prog);
	fprintf(stderr, "Usage: %s option <list_of_ACEs> <file_name>\n", prog);
	fprintf(stderr, "Valid options:\n");
	fprintf(stderr, "\t-v	Version of the program\n");
	fprintf(stderr, "\n\t-a	Add ACE(s), separated by a comma, to an ACL\n");
	fprintf(stderr,
	"\tsetcifsacl -a \"ACL:Administrator:ALLOWED/0x0/FULL\" <file_name>\n");
	fprintf(stderr, "\n");
	fprintf(stderr,
	"\t-D	Delete ACE(s), separated by a comma, from an ACL\n");
	fprintf(stderr,
	"\tsetcifsacl -D \"ACL:Administrator:DENIED/0x0/D\" <file_name>\n");
	fprintf(stderr, "\n");
	fprintf(stderr,
	"\t-M	Modify ACE(s), separated by a comma, in an ACL\n");
	fprintf(stderr,
	"\tsetcifsacl -M \"ACL:user1:ALLOWED/0x0/0x1e01ff\" <file_name>\n");
	fprintf(stderr,
	"\n\t-S	Replace existing ACL with ACE(s), separated by a comma\n");
	fprintf(stderr,
	"\tsetcifsacl -S \"ACL:Administrator:ALLOWED/0x0/D\" <file_name>\n");
	fprintf(stderr, "\nRefer to setcifsacl(8) manpage for details\n");
}

int
main(const int argc, char *const argv[])
{
	int i, rc, c, numcaces, numfaces, maction = -1;
	ssize_t attrlen, bufsize = BUFSIZE;
	char *filename, *attrval, **arrptr = NULL;
	struct cifs_ctrl_acl *daclptr = NULL;
	struct cifs_ace **cacesptr = NULL, **facesptr = NULL;
	struct cifs_ntsd *ntsdptr = NULL;

	openlog(prog, 0, LOG_DAEMON);

	c = getopt(argc, argv, "v:D:M:a:S:?");
	switch (c) {
	case 'v':
		printf("Version: %s\n", VERSION);
		goto out;
	case 'D':
		maction = 0;
		break;
	case 'M':
		maction = 1;
		break;
	case 'a':
		maction = 2;
		break;
	case 'S':
		maction = 3;
		break;
	case '?':
		setcifsacl_usage();
		return 0;
	default:
		break;
	}

	if (argc != 4) {
		setcifsacl_usage();
		return -1;
	}
	filename = argv[3];

	numcaces = get_numcaces(optarg);
	if (!numcaces) {
		printf("%s: No valid ACEs specified\n", __func__);
		return -1;
	}

	arrptr = parse_cmdline_aces(optarg, numcaces);
	if (!arrptr)
		goto setcifsacl_numcaces_ret;

	cacesptr = build_cmdline_aces(arrptr, numcaces);
	if (!cacesptr)
		goto setcifsacl_cmdlineparse_ret;

cifsacl:
	if (bufsize >= XATTR_SIZE_MAX) {
		printf("%s: Buffer size %ld exceeds max size of %d\n",
				__func__, bufsize, XATTR_SIZE_MAX);
		goto setcifsacl_cmdlineverify_ret;
	}

	attrval = malloc(bufsize * sizeof(char));
	if (!attrval) {
		printf("error allocating memory for attribute value buffer\n");
		goto setcifsacl_cmdlineverify_ret;
	}

	attrlen = getxattr(filename, ATTRNAME, attrval, bufsize);
	if (attrlen == -1) {
		if (errno == ERANGE) {
			free(attrval);
			bufsize += BUFSIZE;
			goto cifsacl;
		} else {
			printf("getxattr error: %d\n", errno);
			goto setcifsacl_getx_ret;
		}
	}

	numfaces = get_numfaces((struct cifs_ntsd *)attrval, attrlen, &daclptr);
	if (!numfaces && maction != 2) { /* if we are not adding aces */
		printf("%s: Empty DACL\n", __func__);
		goto setcifsacl_facenum_ret;
	}

	facesptr = build_fetched_aces((char *)daclptr, numfaces);
	if (!facesptr)
		goto setcifsacl_facenum_ret;

	bufsize = 0;
	rc = setacl_action((struct cifs_ntsd *)attrval, &ntsdptr, &bufsize,
		facesptr, numfaces, cacesptr, numcaces, maction);
	if (rc)
		goto setcifsacl_action_ret;

	attrlen = setxattr(filename, ATTRNAME, ntsdptr, bufsize, 0);
	if (attrlen == -1)
		printf("%s: setxattr error: %s\n", __func__, strerror(errno));
	goto setcifsacl_facenum_ret;

out:
	return 0;

setcifsacl_action_ret:
	free(ntsdptr);

setcifsacl_facenum_ret:
	for (i = 0; i < numfaces; ++i)
		free(facesptr[i]);
	free(facesptr);

setcifsacl_getx_ret:
	free(attrval);

setcifsacl_cmdlineverify_ret:
	for (i = 0; i < numcaces; ++i)
		free(cacesptr[i]);
	free(cacesptr);

setcifsacl_cmdlineparse_ret:
	for (i = 0; i < numcaces; ++i)
		free(arrptr[i]);
	free(arrptr);

setcifsacl_numcaces_ret:
	return -1;
}
