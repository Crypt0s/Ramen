/*
 * Credentials stashing utility for Linux CIFS VFS (virtual filesystem) client
 * Copyright (C) 2010 Jeff Layton (jlayton@samba.org)
 * Copyright (C) 2010 Igor Druzhinin (jaxbrigs@gmail.com)
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif /* HAVE_CONFIG_H */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <ctype.h>
#include <keyutils.h>
#include "mount.h"
#include "resolve_host.h"

#define THIS_PROGRAM_NAME "cifscreds"

/* max length of appropriate command */
#define MAX_COMMAND_SIZE 32

/* max length of username, password and domain name */
#define MAX_USERNAME_SIZE 32
#define MOUNT_PASSWD_SIZE 128
#define MAX_DOMAIN_SIZE 64

/* allowed and disallowed characters for user and domain name */
#define USER_DISALLOWED_CHARS "\\/\"[]:|<>+=;,?*@"
#define DOMAIN_ALLOWED_CHARS "abcdefghijklmnopqrstuvwxyz" \
			     "ABCDEFGHIJKLMNOPQRSTUVWXYZ-."

/* destination keyring */
#define DEST_KEYRING KEY_SPEC_USER_KEYRING

struct command {
	int (*action)(int argc, char *argv[]);
	const char	name[MAX_COMMAND_SIZE];
	const char	*format;
};

static int cifscreds_add(int argc, char *argv[]);
static int cifscreds_clear(int argc, char *argv[]);
static int cifscreds_clearall(int argc, char *argv[]);
static int cifscreds_update(int argc, char *argv[]);

const char *thisprogram;

struct command commands[] = {
	{ cifscreds_add,	"add",		"<host> <user> [domain]" },
	{ cifscreds_clear,	"clear",	"<host> <user> [domain]" },
	{ cifscreds_clearall,	"clearall",	"" },
	{ cifscreds_update,	"update",	"<host> <user> [domain]" },
	{ NULL, "", NULL }
};

/* display usage information */
static void usage(void)
{
	struct command *cmd;

	fprintf(stderr, "Usage:\n");
	for (cmd = commands; cmd->action; cmd++)
		fprintf(stderr, "\t%s %s %s\n", thisprogram,
			cmd->name, cmd->format);
	fprintf(stderr, "\n");

	exit(EXIT_FAILURE);
}

/* create key's description string from given credentials */
static char *
create_description(const char *addr, const char *user,
		   const char *domain, char *desc)
{
	char *str_end;
	int str_len;

	sprintf(desc, "%s:%s:%s:", THIS_PROGRAM_NAME, addr, user);

	if (domain != NULL) {
		str_end = desc + strnlen(desc, INET6_ADDRSTRLEN + \
					+ MAX_USERNAME_SIZE + \
					+ sizeof(THIS_PROGRAM_NAME) + 3);
		str_len = strnlen(domain, MAX_DOMAIN_SIZE);
		while (str_len--) {
			*str_end = tolower(*domain++);
			str_end++;
		}
		*str_end = '\0';
	}

	return desc;
}

/* search a specific key in keyring */
static key_serial_t
key_search(const char *addr, const char *user, const char *domain)
{
	char desc[INET6_ADDRSTRLEN + MAX_USERNAME_SIZE + MAX_DOMAIN_SIZE + \
		+ sizeof(THIS_PROGRAM_NAME) + 3];
	key_serial_t key, *pk;
	void *keylist;
	char *buffer;
	int count, dpos, n, ret;

	create_description(addr, user, domain, desc);

	/* read the key payload data */
	count = keyctl_read_alloc(DEST_KEYRING, &keylist);
	if (count < 0)
		return 0;

	count /= sizeof(key_serial_t);

	if (count == 0) {
		ret = 0;
		goto key_search_out;
	}

	/* list the keys in the keyring */
	pk = keylist;
	do {
		key = *pk++;

		ret = keyctl_describe_alloc(key, &buffer);
		if (ret < 0)
			continue;

		n = sscanf(buffer, "%*[^;];%*d;%*d;%*x;%n", &dpos);
		if (n) {
			free(buffer);
			continue;
		}

		if (!strcmp(buffer + dpos, desc)) {
			ret = key;
			free(buffer);
			goto key_search_out;
		}
		free(buffer);

	} while (--count);

	ret = 0;

key_search_out:
	free(keylist);
	return ret;
}

/* search all program's keys in keyring */
static key_serial_t key_search_all(void)
{
	key_serial_t key, *pk;
	void *keylist;
	char *buffer;
	int count, dpos, n, ret;

	/* read the key payload data */
	count = keyctl_read_alloc(DEST_KEYRING, &keylist);
	if (count < 0)
		return 0;

	count /= sizeof(key_serial_t);

	if (count == 0) {
		ret = 0;
		goto key_search_all_out;
	}

	/* list the keys in the keyring */
	pk = keylist;
	do {
		key = *pk++;

		ret = keyctl_describe_alloc(key, &buffer);
		if (ret < 0)
			continue;

		n = sscanf(buffer, "%*[^;];%*d;%*d;%*x;%n", &dpos);
		if (n) {
			free(buffer);
			continue;
		}

		if (strstr(buffer + dpos, THIS_PROGRAM_NAME ":") ==
			buffer + dpos
		) {
			ret = key;
			free(buffer);
			goto key_search_all_out;
		}
		free(buffer);

	} while (--count);

	ret = 0;

key_search_all_out:
	free(keylist);
	return ret;
}

/* add or update a specific key to keyring */
static key_serial_t
key_add(const char *addr, const char *user,
	const char *domain, const char *pass)
{
	char desc[INET6_ADDRSTRLEN + MAX_USERNAME_SIZE + MAX_DOMAIN_SIZE + \
		+ sizeof(THIS_PROGRAM_NAME) + 3];

	create_description(addr, user, domain, desc);

	return add_key("user", desc, pass, strnlen(pass, MOUNT_PASSWD_SIZE) + 1,
		DEST_KEYRING);
}

/* add command handler */
static int cifscreds_add(int argc, char *argv[])
{
	char addrstr[MAX_ADDR_LIST_LEN];
	char *currentaddress, *nextaddress;
	char *pass;
	int ret;

	if (argc != 4 && argc != 5)
		usage();

	ret = resolve_host(argv[2], addrstr);
	switch (ret) {
	case EX_USAGE:
		fprintf(stderr, "error: Could not resolve address "
			"for %s\n", argv[2]);
		return EXIT_FAILURE;

	case EX_SYSERR:
		fprintf(stderr, "error: Problem parsing address list\n");
		return EXIT_FAILURE;
	}

	if (strpbrk(argv[3], USER_DISALLOWED_CHARS)) {
		fprintf(stderr, "error: Incorrect username\n");
		return EXIT_FAILURE;
	}

	if (argc == 5) {
		if (strspn(argv[4], DOMAIN_ALLOWED_CHARS) !=
			strnlen(argv[4], MAX_DOMAIN_SIZE)
		) {
			fprintf(stderr, "error: Incorrect domain name\n");
			return EXIT_FAILURE;
		}
	}

	/* search for same credentials stashed for current host */
	currentaddress = addrstr;
	nextaddress = strchr(currentaddress, ',');
	if (nextaddress)
		*nextaddress++ = '\0';

	while (currentaddress) {
		if (key_search(currentaddress, argv[3],
			argc == 5 ? argv[4] : NULL) > 0
		) {
			printf("You already have stashed credentials "
				"for %s (%s)\n", currentaddress, argv[2]);
			printf("If you want to update them use:\n");
			printf("\t%s update\n", thisprogram);

			return EXIT_FAILURE;
		}

		currentaddress = nextaddress;
		if (currentaddress) {
			*(currentaddress - 1) = ',';
			nextaddress = strchr(currentaddress, ',');
			if (nextaddress)
				*nextaddress++ = '\0';
		}
	}

	/*
	 * if there isn't same credentials stashed add them to keyring
	 * and set permisson mask
	 */
	pass = getpass("Password: ");

	currentaddress = addrstr;
	nextaddress = strchr(currentaddress, ',');
	if (nextaddress)
		*nextaddress++ = '\0';

	while (currentaddress) {
		key_serial_t key = key_add(currentaddress, argv[3],
					   argc == 5 ? argv[4] : NULL, pass);
		if (key <= 0) {
			fprintf(stderr, "error: Add credential key for %s\n",
				currentaddress);
		} else {
			if (keyctl(KEYCTL_SETPERM, key, KEY_POS_VIEW | \
				KEY_POS_WRITE | KEY_USR_VIEW | \
				KEY_USR_WRITE) < 0
			) {
				fprintf(stderr, "error: Setting permissons "
					"on key, attempt to delete...\n");

				if (keyctl(KEYCTL_UNLINK, key, DEST_KEYRING) < 0) {
					fprintf(stderr, "error: Deleting key from "
						"keyring for %s (%s)\n",
						currentaddress, argv[2]);
				}
			}
		}

		currentaddress = nextaddress;
		if (currentaddress) {
			nextaddress = strchr(currentaddress, ',');
			if (nextaddress)
				*nextaddress++ = '\0';
		}
	}

	return EXIT_SUCCESS;
}

/* clear command handler */
static int cifscreds_clear(int argc, char *argv[])
{
	char addrstr[MAX_ADDR_LIST_LEN];
	char *currentaddress, *nextaddress;
	int ret, count = 0, errors = 0;

	if (argc != 4 && argc != 5)
		usage();

	ret = resolve_host(argv[2], addrstr);
	switch (ret) {
	case EX_USAGE:
		fprintf(stderr, "error: Could not resolve address "
			"for %s\n", argv[2]);
		return EXIT_FAILURE;

	case EX_SYSERR:
		fprintf(stderr, "error: Problem parsing address list\n");
		return EXIT_FAILURE;
	}

	if (strpbrk(argv[3], USER_DISALLOWED_CHARS)) {
		fprintf(stderr, "error: Incorrect username\n");
		return EXIT_FAILURE;
	}

	if (argc == 5) {
		if (strspn(argv[4], DOMAIN_ALLOWED_CHARS) !=
			strnlen(argv[4], MAX_DOMAIN_SIZE)
		) {
			fprintf(stderr, "error: Incorrect domain name\n");
			return EXIT_FAILURE;
		}
	}

	/*
	 * search for same credentials stashed for current host
	 * and unlink them from session keyring
	 */
	currentaddress = addrstr;
	nextaddress = strchr(currentaddress, ',');
	if (nextaddress)
		*nextaddress++ = '\0';

	while (currentaddress) {
		key_serial_t key = key_search(currentaddress, argv[3],
						argc == 5 ? argv[4] : NULL);
		if (key > 0) {
			if (keyctl(KEYCTL_UNLINK, key, DEST_KEYRING) < 0) {
				fprintf(stderr, "error: Removing key from "
					"keyring for %s (%s)\n",
					currentaddress, argv[2]);
				errors++;
			} else {
				count++;
			}
		}

		currentaddress = nextaddress;
		if (currentaddress) {
			nextaddress = strchr(currentaddress, ',');
			if (nextaddress)
				*nextaddress++ = '\0';
		}
	}

	if (!count && !errors) {
		printf("You have no same stashed credentials "
			" for %s\n", argv[2]);
		printf("If you want to add them use:\n");
		printf("\t%s add\n", thisprogram);

		return EXIT_FAILURE;
	}

	return EXIT_SUCCESS;
}

/* clearall command handler */
static int cifscreds_clearall(int argc, char *argv[])
{
	key_serial_t key;
	int count = 0, errors = 0;

	if (argc != 2)
		usage();

	/*
	 * search for all program's credentials stashed in session keyring
	 * and then unlink them
	 */
	do {
		key = key_search_all();
		if (key > 0) {
			if (keyctl(KEYCTL_UNLINK, key, DEST_KEYRING) < 0) {
				fprintf(stderr, "error: Deleting key "
					"from keyring");
				errors++;
			} else {
				count++;
			}
		}
	} while (key > 0);

	if (!count && !errors) {
		printf("You have no stashed " THIS_PROGRAM_NAME
			" credentials\n");
		printf("If you want to add them use:\n");
		printf("\t%s add\n", thisprogram);

		return EXIT_FAILURE;
	}

	return EXIT_SUCCESS;
}

/* update command handler */
static int cifscreds_update(int argc, char *argv[])
{
	char addrstr[MAX_ADDR_LIST_LEN];
	char *currentaddress, *nextaddress, *pass;
	char *addrs[16];
	int ret, id, count = 0;

	if (argc != 4 && argc != 5)
		usage();

	ret = resolve_host(argv[2], addrstr);
	switch (ret) {
	case EX_USAGE:
		fprintf(stderr, "error: Could not resolve address "
			"for %s\n", argv[2]);
		return EXIT_FAILURE;

	case EX_SYSERR:
		fprintf(stderr, "error: Problem parsing address list\n");
		return EXIT_FAILURE;
	}

	if (strpbrk(argv[3], USER_DISALLOWED_CHARS)) {
		fprintf(stderr, "error: Incorrect username\n");
		return EXIT_FAILURE;
	}

	if (argc == 5) {
		if (strspn(argv[4], DOMAIN_ALLOWED_CHARS) !=
			strnlen(argv[4], MAX_DOMAIN_SIZE)
		) {
			fprintf(stderr, "error: Incorrect domain name\n");
			return EXIT_FAILURE;
		}
	}

	/* search for necessary credentials stashed in session keyring */
	currentaddress = addrstr;
	nextaddress = strchr(currentaddress, ',');
	if (nextaddress)
		*nextaddress++ = '\0';

	while (currentaddress) {
		if (key_search(currentaddress, argv[3],
			argc == 5 ? argv[4] : NULL) > 0
		) {
			addrs[count] = currentaddress;
			count++;
		}

		currentaddress = nextaddress;
		if (currentaddress) {
			nextaddress = strchr(currentaddress, ',');
			if (nextaddress)
				*nextaddress++ = '\0';
		}
	}

	if (!count) {
		printf("You have no same stashed credentials "
			"for %s\n", argv[2]);
		printf("If you want to add them use:\n");
		printf("\t%s add\n", thisprogram);

		return EXIT_FAILURE;
	}

	/* update payload of found keys */
	pass = getpass("Password: ");

	for (id = 0; id < count; id++) {
		key_serial_t key = key_add(addrs[id], argv[3],
					argc == 5 ? argv[4] : NULL, pass);
		if (key <= 0)
			fprintf(stderr, "error: Update credential key "
				"for %s\n", addrs[id]);
	}

	return EXIT_SUCCESS;
}

int main(int argc, char **argv)
{
	struct command *cmd, *best;
	int n;

	thisprogram = (char *)basename(argv[0]);
	if (thisprogram == NULL)
		thisprogram = THIS_PROGRAM_NAME;

	if (argc == 1)
		usage();

	/* find the best fit command */
	best = NULL;
	n = strnlen(argv[1], MAX_COMMAND_SIZE);

	for (cmd = commands; cmd->action; cmd++) {
		if (memcmp(cmd->name, argv[1], n) != 0)
			continue;

		if (cmd->name[n] == 0) {
			/* exact match */
			best = cmd;
			break;
		}

		/* partial match */
		if (best) {
			fprintf(stderr, "Ambiguous command\n");
			exit(EXIT_FAILURE);
		}

		best = cmd;
	}

	if (!best) {
		fprintf(stderr, "Unknown command\n");
		exit(EXIT_FAILURE);
	}

	exit(best->action(argc, argv));
}
