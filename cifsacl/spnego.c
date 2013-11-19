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

#include <talloc.h>
#include <stdint.h>

#include "replace.h"
#include "data_blob.h"
#include "asn1.h"
#include "spnego.h"

/*
  generate a krb5 GSS-API wrapper packet given a ticket
*/
DATA_BLOB spnego_gen_krb5_wrap(const DATA_BLOB ticket, const uint8_t tok_id[2])
{
	ASN1_DATA *data;
	DATA_BLOB ret;
	TALLOC_CTX *mem_ctx = talloc_init("gssapi");

	data = asn1_init(mem_ctx);
	if (data == NULL) {
		return data_blob_null;
	}

	asn1_push_tag(data, ASN1_APPLICATION(0));
	asn1_write_OID(data, OID_KERBEROS5);

	asn1_write(data, tok_id, 2);
	asn1_write(data, ticket.data, ticket.length);
	asn1_pop_tag(data);

#if 0
	if (data->has_error) {
		DEBUG(1,("Failed to build krb5 wrapper at offset %d\n", (int)data->ofs));
	}
#endif

	ret = data_blob(data->data, data->length);
	asn1_free(data);
	talloc_free(mem_ctx);

	return ret;
}

/*
  Generate a negTokenInit as used by the client side ... It has a mechType
  (OID), and a mechToken (a security blob) ... 

  Really, we need to break out the NTLMSSP stuff as well, because it could be
  raw in the packets!
*/
DATA_BLOB gen_negTokenInit(const char *OID, DATA_BLOB blob)
{
	ASN1_DATA *data;
	DATA_BLOB ret;
	TALLOC_CTX *mem_ctx = talloc_init("spnego");

	data = asn1_init(mem_ctx);
	if (data == NULL) {
		return data_blob_null;
	}

	asn1_push_tag(data, ASN1_APPLICATION(0));
	asn1_write_OID(data,OID_SPNEGO);
	asn1_push_tag(data, ASN1_CONTEXT(0));
	asn1_push_tag(data, ASN1_SEQUENCE(0));

	asn1_push_tag(data, ASN1_CONTEXT(0));
	asn1_push_tag(data, ASN1_SEQUENCE(0));
	asn1_write_OID(data, OID);
	asn1_pop_tag(data);
	asn1_pop_tag(data);

	asn1_push_tag(data, ASN1_CONTEXT(2));
	asn1_write_OctetString(data,blob.data,blob.length);
	asn1_pop_tag(data);

	asn1_pop_tag(data);
	asn1_pop_tag(data);

	asn1_pop_tag(data);

#if 0
	if (data->has_error) {
		DEBUG(1,("Failed to build negTokenInit at offset %d\n", (int)data->ofs));
	}
#endif

	ret = data_blob(data->data, data->length);
	asn1_free(data);
	talloc_free(mem_ctx);

	return ret;
}

