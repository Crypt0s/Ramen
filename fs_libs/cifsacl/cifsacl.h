/*
* Header file for getcifsacl and setcifsacl utilities
*
* Copyright (C) Shirish Pargaonkar (shirishp@us.ibm.com) 2011
*
* Has various access rights, security descriptor fields defines
* and data structures related to security descriptor, DACL, ACE,
* and SID.
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

#ifndef _CIFSACL_H
#define _CIFSACL_H

#define BUFSIZE 1024
#define ATTRNAME "system.cifs_acl"

#define MAX_NUM_AUTHS 6

/* File specific rights */
#define READ_DATA	0x00000001 /* R */
#define WRITE_DATA	0x00000002 /* W */
#define APPEND_DATA	0x00000004 /* A */
#define READ_EA		0x00000008 /* REA */
#define WRITE_EA	0x00000010 /* WEA */
#define EXEC		0x00000020 /* E */
#define DELDHLD		0x00000040 /* DC */
#define READ_ATTR	0x00000080 /* RA */
#define WRITE_ATTR	0x00000100 /* WA */

/* Standard rights */
#define DELETE		0x00010000 /* D */
#define READ_CONTROL	0x00020000 /* RC */
#define WRITE_DAC	0x00040000 /* P */
#define WRITE_OWNER	0x00080000 /* O */
#define SYNC		0x00100000 /* S */

/* Generic rights */
#define SYSSEC		0x01000000
#define MAX		0x02000000
#define ALL		0x10000000
#define EXECUTE		0x20000000 /* GE */
#define WRITE		0x40000000 /* GW */
#define READ		0x80000000 /* GR */

/* D | RC | P | O | S | R | W | A | E | DC | REA | WEA | RA | WA  */
#define FULL_CONTROL	0x001f01ff

/* RC | S | R | E | REA | RA */
#define EREAD		0x001200a9

/* RC | S | R | E | REA | GR | GE */
#define OREAD		0xa01200a1

/* RC | S | R | REA | RA */
#define BREAD		0x00120089

/* W | A | WA | WEA| */
#define EWRITE		0x00000116

/* D | RC | S | R | W | A | E |REA | WEA | RA | WA */
#define CHANGE		0x001301bf

/* GR | RC | REA | RA | REA | R */
#define ALL_READ_BITS	0x80020089

/* WA | WEA | A | W */
#define ALL_WRITE_BITS	0x40000116

#define OBJECT_INHERIT_FLAG 0x01	/* OI */
#define CONTAINER_INHERIT_FLAG 0x02	/* CI */
#define NO_PROPAGATE_INHERIT_FLAG 0x04	/* NP */
#define INHERIT_ONLY_FLAG 0x08		/* IO */
#define INHERITED_ACE_FLAG 0x10		/* I */
#define VFLAGS 0x1f

#define ACCESS_ALLOWED	0		/* ALLOWED */
#define ACCESS_DENIED	1		/* DENIED */
#define ACCESS_ALLOWED_OBJECT	5	/* OBJECT_ALLOWED */
#define ACCESS_DENIED_OBJECT	6	/* OBJECT_DENIED */

#define COMPSID 0x1
#define COMPTYPE 0x2
#define COMPFLAG 0x4
#define COMPMASK 0x8
#define COMPALL 0xf /* COMPSID | COMPTYPE | COMPFLAG | COMPMASK */

enum ace_action {
	acedelete = 0,
	acemodify,
	aceadd,
	aceset
};

struct cifs_ntsd {
	uint16_t revision; /* revision level */
	uint16_t type;
	uint32_t osidoffset;
	uint32_t gsidoffset;
	uint32_t sacloffset;
	uint32_t dacloffset;
};

struct cifs_sid {
	uint8_t revision; /* revision level */
	uint8_t num_subauth;
	uint8_t authority[6];
	uint32_t sub_auth[5]; /* sub_auth[num_subauth] */
};

struct cifs_ctrl_acl {
	uint16_t revision; /* revision level */
	uint16_t size;
	uint32_t num_aces;
};

struct cifs_ace {
	uint8_t type;
	uint8_t flags;
	uint16_t size;
	uint32_t access_req;
	struct cifs_sid sid; /* ie UUID of user or group who gets these perms */
};

#endif /* CIFSACL_H */
