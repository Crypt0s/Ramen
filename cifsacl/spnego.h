/* 
   Unix SMB/CIFS implementation.
   simple kerberos5/SPNEGO routines
   Copyright (C) Andrew Tridgell 2001
   Copyright (C) Jim McDonough <jmcd@us.ibm.com> 2002
   Copyright (C) Luke Howard     2003
   
   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 3 of the License, or
   (at your option) any later version.
   
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
   
   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#ifndef  _SPNEGO_H
#define  _SPNEGO_H

/* needed OID's */
#define OID_SPNEGO "1.3.6.1.5.5.2"
#define OID_NTLMSSP "1.3.6.1.4.1.311.2.2.10"
#define OID_KERBEROS5_OLD "1.2.840.48018.1.2.2"
#define OID_KERBEROS5 "1.2.840.113554.1.2.2"

/* not really SPNEGO but GSSAPI (RFC 1964) */
#define TOK_ID_KRB_AP_REQ	(unsigned char *)"\x01\x00"
#define TOK_ID_KRB_AP_REP	(unsigned char *)"\x02\x00"
#define TOK_ID_KRB_ERROR	(unsigned char *)"\x03\x00"
#define TOK_ID_GSS_GETMIC	(unsigned char *)"\x01\x01"
#define TOK_ID_GSS_WRAP		(unsigned char *)"\x02\x01"

extern DATA_BLOB gen_negTokenInit(const char *OID, DATA_BLOB blob);
extern DATA_BLOB spnego_gen_krb5_wrap(const DATA_BLOB ticket, const uint8_t tok_id[2]);

#endif /* _SPNEGO_H */
