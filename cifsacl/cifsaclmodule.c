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
#include <ctype.h>
#include <Python.h>
#include <sys/xattr.h>
#include <wbclient.h>
#include "cifsacl.h"

#define MSG_ERRORS_LENGTH 60


/*********************************************************/
/* GLOBALS VARIABLES */
/*********************************************************/
static PyObject *CIFSaclError;


/*********************************************************/
/* METHODS */
/*********************************************************/


static void
print_each_ace_mask(uint32_t mask)
{
	if ((mask & ALL_READ_BITS) && ((mask & EREAD) != EREAD &&
			(mask & OREAD) != OREAD && (mask & BREAD) != BREAD)) {
		printf("0x%x", mask);
		return;
	}

	if ((mask & ALL_WRITE_BITS) && (mask & EWRITE) != EWRITE) {
		printf("0x%x", mask);
		return;
	}

	if ((mask & EREAD) == EREAD || (mask & OREAD) == OREAD ||
			(mask & BREAD) == BREAD)
		printf("R");
	if ((mask & EWRITE) == EWRITE)
		printf("W");
	if ((mask & EXEC) == EXEC)
		printf("X");
	if ((mask & DELETE) == DELETE)
		printf("D");
	if ((mask & WRITE_DAC) == WRITE_DAC)
		printf("P");
	if ((mask & WRITE_OWNER) == WRITE_OWNER)
		printf("O");
}

static void
print_ace_mask(uint32_t mask, int raw)
{
	if (raw) {
		printf("0x%x\n", mask);
		return;
	}

	if (mask == FULL_CONTROL)
		printf("FULL");
	else if (mask == CHANGE)
		printf("CHANGE");
	else if (mask == DELETE)
		printf("D");
	else if (mask == EREAD)
		printf("READ");
	else if (mask & DELDHLD)
		printf("0x%x", mask);
	else
		print_each_ace_mask(mask);

	printf("\n");
	return;
}

static void
get_ace_mask(uint32_t mask, int raw,char *py_ace_string)
{
	raw = 0;
        char *st10 = malloc(50);


	if (raw) {
        	sprintf(st10, "::0x%x", mask);
                strcat(py_ace_string,st10);
		return;
	}

	if (mask == FULL_CONTROL){
		sprintf(st10,"::FULL");
                strcat(py_ace_string,st10);
	}
	else if (mask == CHANGE){
		sprintf(st10,"::CHANGE");
                strcat(py_ace_string,st10);
	}
	else if (mask == DELETE){
		sprintf(st10,"::D");
                strcat(py_ace_string,st10);
	}
	else if  (mask == EREAD){
		sprintf(st10,"::READ");
                strcat(py_ace_string,st10);
	}
	else if (mask & DELDHLD) {
		sprintf(st10,"::0x%x", mask);
                strcat(py_ace_string,st10);
	}
	return;
}

static void
print_ace_flags(uint8_t flags, int raw)
{
	bool mflags = false;

	if (raw) {
		printf("0x%x", flags);
		return;
	}

	if (flags & OBJECT_INHERIT_FLAG) {
		if (mflags)
			printf("|");
		else
			mflags = true;
		printf("OI");
	}
	if (flags & CONTAINER_INHERIT_FLAG) {
		if (mflags)
			printf("|");
		else
			mflags = true;
		printf("CI");
	}
	if (flags & NO_PROPAGATE_INHERIT_FLAG) {
		if (mflags)
			printf("|");
		else
			mflags = true;
		printf("NP");
	}
	if (flags & INHERIT_ONLY_FLAG) {
		if (mflags)
			printf("|");
		else
			mflags = true;
		printf("IO");
	}
	if (flags & INHERITED_ACE_FLAG) {
		if (mflags)
			printf("|");
		else
			mflags = true;
		printf("I");
	}

	if (!mflags)
		printf("0x0");
}

static void
print_ace_type(uint8_t acetype, int raw)
{
	if (raw) {
		printf("0x%x", acetype);
		return;
	}

	switch (acetype) {
	case ACCESS_ALLOWED:
		printf("ALLOWED");
		break;
	case ACCESS_DENIED:
		printf("DENIED");
		break;
	case ACCESS_ALLOWED_OBJECT:
		printf("OBJECT_ALLOWED");
		break;
	case ACCESS_DENIED_OBJECT:
		printf("OBJECT_DENIED");
		break;
	default:
		printf("UNKNOWN");
		break;
	}
}

static void
get_ace_type(uint8_t acetype, int raw, char *py_ace_string)
{
	raw=0;
	char *st10 = malloc(50);
	if (raw) {
                sprintf(st10, "::0x%x", acetype);
		strcat(py_ace_string,st10);

		//printf("0x%x", acetype);
		return;
	}

	switch (acetype) {
	case ACCESS_ALLOWED:
                sprintf(st10, "::ALLOWED");
                strcat(py_ace_string,st10);
		break;
	case ACCESS_DENIED:
                sprintf(st10, "::DENIED");
                strcat(py_ace_string,st10);
		break;
	default:
		printf("UNKNOWN");
		break;
	}
}

static PyObject *
get_sid(struct wbcDomainSid *sidptr, int raw,char *py_ace_string)
{
	int i;
	int num_auths;
	int num_auth = MAX_NUM_AUTHS;
	wbcErr rc;
	char *domain_name = NULL;
	char *sidname = NULL;
	enum wbcSidType sntype;

	if (raw)
		goto get_sid_raw;
	
get_sid_raw:
	num_auths = sidptr->num_auths;
	//printf("S\n");
	int ret;
	char *st1 = malloc(50);
        char *st2 = malloc(50);
        char *st3 = malloc(50);
        char *st4 = malloc(50);
	
	ret = sprintf(st1,"S-%d",sidptr->sid_rev_num);
	for (i = 0; i < num_auth; ++i)
		if (sidptr->id_auth[i]){
			sprintf(st3, "-%d", sidptr->id_auth[i]);
			strcat(st1,st3);
		}
	for (i = 0; i < num_auths; i++) {
		sprintf(st4,"-%u", le32toh(sidptr->sub_auths[i]));
		strcat(st1,st4);
	}
        
	strcpy(py_ace_string, st1);
        //PyList_Append(py_acl_list, py_title);
        //return py_title;
}
static void
print_sid(struct wbcDomainSid *sidptr, int raw,PyObject *py_acl_list)
{
	int i;
	int num_auths;
	int num_auth = MAX_NUM_AUTHS;
	wbcErr rc;
	char *domain_name = NULL;
	char *sidname = NULL;
	enum wbcSidType sntype;

	if (raw)
		goto print_sid_raw;
	
	//rc = wbcLookupSid(sidptr, &domain_name, &sidname, &sntype);
	if (!rc) {
		printf("%s", domain_name);
		if (strlen(domain_name))
			printf("%c", '\\');
		printf("%s", sidname);
		return;
	}

print_sid_raw:
	num_auths = sidptr->num_auths;
	//printf("S\n");
	int ret;
	char *st1 = malloc(50);
        char *st2 = malloc(50);
        char *st3 = malloc(50);
        char *st4 = malloc(50);

	ret = sprintf(st1,"S-%d",sidptr->sid_rev_num);
	for (i = 0; i < num_auth; ++i)
		if (sidptr->id_auth[i]){
			sprintf(st3, "-%d", sidptr->id_auth[i]);
			strcat(st1,st3);
		}
	for (i = 0; i < num_auths; i++) {
		sprintf(st4,"-%u", le32toh(sidptr->sub_auths[i]));
		strcat(st1,st4);
	}
        PyObject * py_title;
        py_title = Py_BuildValue("s", st1);
        PyList_Append(py_acl_list, py_title);
	free(st1);
	free(st2);
	free(st3);
	free(st4);
}

static void
print_ace(struct cifs_ace *pace, char *end_of_acl, int raw,PyObject *py_acl_list)
{
	/* validate that we do not go past end of acl */
	if (le16toh(pace->size) < 16)
		return;

	if (end_of_acl < (char *)pace + le16toh(pace->size))
		return;
	//bernz change
	//print_sid to become +get_sid, pass string
	//add bottom stuff to string
	//add string to py_acl_list
	char *py_ace_string = malloc(200);
	get_sid((struct wbcDomainSid *)&pace->sid, raw,py_ace_string);
	//print_sid((struct wbcDomainSid *)&pace->sid, raw,py_acl_list);
	get_ace_type(pace->type, raw,py_ace_string);
	//prtintf("/");
	//print_ace_flags(pace->flags, raw);
	//printf("/");
	get_ace_mask(pace->access_req, raw,py_ace_string);

        PyObject * py_title;
        py_title = Py_BuildValue("s", py_ace_string);
        PyList_Append(py_acl_list, py_title);


	return;
}


static void
parse_dacl(struct cifs_ctrl_acl *pdacl, char *end_of_acl, int raw,PyObject *py_acl_list)
{
	int i;
	int num_aces = 0;
	int acl_size;
	char *acl_base;
	struct cifs_ace *pace;

	if (!pdacl)
		return;

	if (end_of_acl < (char *)pdacl + le16toh(pdacl->size))
		return;

	acl_base = (char *)pdacl;
	acl_size = sizeof(struct cifs_ctrl_acl);

	num_aces = le32toh(pdacl->num_aces);
	if (num_aces  > 0) {
		for (i = 0; i < num_aces; ++i) {
			pace = (struct cifs_ace *) (acl_base + acl_size);
			print_ace(pace, end_of_acl, raw,py_acl_list);
			acl_base = (char *)pace;
			acl_size = le16toh(pace->size);
		}
	}

	return;
}

static int
parse_sid(struct wbcDomainSid *psid, char *end_of_acl, char *title, int raw,PyObject *py_acl_list)
{
	if (end_of_acl < (char *)psid + 8)
		return -EINVAL;
	//if (title)
	//	printf("%s:", title);
	print_sid((struct wbcDomainSid *)psid, raw,py_acl_list);
	//printf("\n");
	

	return 0;
}


static int
parse_sec_desc(struct cifs_ntsd *pntsd, ssize_t acl_len, int raw, PyObject *py_acl_list)
{
	int rc;
	uint32_t dacloffset;
	char *end_of_acl = ((char *)pntsd) + acl_len;
	struct wbcDomainSid *owner_sid_ptr, *group_sid_ptr;
	struct cifs_ctrl_acl *dacl_ptr; /* no need for SACL ptr */

	if (pntsd == NULL)
		return -EIO;

	owner_sid_ptr = (struct wbcDomainSid *)((char *)pntsd +
				le32toh(pntsd->osidoffset));
	group_sid_ptr = (struct wbcDomainSid *)((char *)pntsd +
				le32toh(pntsd->gsidoffset));
	dacloffset = le32toh(pntsd->dacloffset);
	dacl_ptr = (struct cifs_ctrl_acl *)((char *)pntsd + dacloffset);
	//printf("REVISION:0x%x\n", pntsd->revision);
	//printf("CONTROL:0x%x\n", pntsd->type);
	
	rc = parse_sid(owner_sid_ptr, end_of_acl, "OWNER", raw,py_acl_list);
	if (rc)
		return rc;
	rc = parse_sid(group_sid_ptr, end_of_acl, "GROUP", raw,py_acl_list);
	if (rc)
		return rc;

	if (dacloffset)
		parse_dacl(dacl_ptr, end_of_acl, raw,py_acl_list);
	else
		printf("No ACL\n"); /* BB grant all or default perms? */

	return 0;
}


/*
 *  get the contents of an nfs4 ACL
 *
 *  Permission mapping:
 *  r - NFS4_ACE_READ_DATA
 *  l - NFS4_ACE_LIST_DIRECTORY
 *  w - NFS4_ACE_WRITE_DATA
 *  f - NFS4_ACE_ADD_FILE
 *  a - NFS4_ACE_APPEND_DATA
 *  s - NFS4_ACE_ADD_SUBDIRECTORY
 *  n - NFS4_ACE_READ_NAMED_ATTRS
 *  N - NFS4_ACE_WRITE_NAMED_ATTRS
 *  x - NFS4_ACE_EXECUTE
 *  D - NFS4_ACE_DELETE_CHILD
 *  t - NFS4_ACE_READ_ATTRIBUTES
 *  T - NFS4_ACE_WRITE_ATTRIBUTES
 *  d - NFS4_ACE_DELETE
 *  c - NFS4_ACE_READ_ACL
 *  C - NFS4_ACE_WRITE_ACL
 *  o - NFS4_ACE_WRITE_OWNER
 *  y - NFS4_ACE_SYNCHRONIZE
 *
 *  returns : [ace1, ace2,...]
 *  where
 * ace <=> {"type"        : type,
 *          "whotype"     : whotype,
 *          "flags"        : flags,
 *          "access_mask" : access_mask,
 *          "who"         : who
 *         }
 */
static PyObject *
cifsacl_getfacl(PyObject *self, PyObject *args)
{
  const char      *path;
  struct cifs_ctl_acl *acl;
  struct cifs_ace *ace;
  int             ace_count;
  char            errors[16];
  char            type[16];
  char            flags[16];
  char            who[30];
  char            access[16];


  /* python objects */
  PyObject * py_acl_list;

  if (!PyArg_ParseTuple(args, "s", &path))
    return NULL;

  int c, raw = 1;
  ssize_t attrlen;
  size_t bufsize = BUFSIZE;
  char *attrval;

  attrval = malloc(bufsize * sizeof(char));
  attrlen = getxattr(path, ATTRNAME, attrval, bufsize);
  py_acl_list = PyList_New(0);

  parse_sec_desc((struct cifs_ntsd *)attrval, attrlen, raw, py_acl_list);
  free(attrval);



  /* get acls*/
//  acl = nfs4_acl_for_path(path);
//  if (acl == NULL) {
//    PyErr_SetString(CIFSaclError, "Invalid filename");
//    return NULL;
//  }
//
//  /* put all ACEs in a python list */
//  ace_count = 1;
//  ace = nfs4_get_first_ace(acl);
//  /* create the list containing the ACEs */
//  py_acl_list = PyList_New(0);
//
//  while (1) {
//    if (ace == NULL) {
//      if (acl->naces > ace_count) {
//	/* unexp_failed*/
//	PyErr_SetString(CIFSaclError, "Unexp failed");
//	return NULL;
//      }
//      else
//	break;
//    }
//
//    /* create a dictionary containing the ace */
//    /* ace <=> {"type"    : type,             */
//    /*          "whotype" : whotype,          */
//    /*          ...                           */
//    /*         }                              */
//    py_ace_dict = PyDict_New();
//    if (nfs4_ace_to_string(errors, ace, acl->is_directory,
//			   type, flags, who, access)) {
//      /* if failure (==1) */
//      PyErr_SetString(CIFSaclError, errors);
//      return NULL;
//    }
//
//    /* create the Python objects : keys and values*/
//    py_type_key          = Py_BuildValue("s", "type");
//    py_type_value        = Py_BuildValue("s", type);
//    py_whotype_key       = Py_BuildValue("s", "whotype");
//    py_whotype_value     = Py_BuildValue("I", ace->whotype);
//    py_flags_key         = Py_BuildValue("s", "flags");
//    py_flags_value       = Py_BuildValue("s", flags);
//    py_access_mask_key   = Py_BuildValue("s", "access_mask");
//    py_access_mask_value = Py_BuildValue("s", access);
//    py_who_key           = Py_BuildValue("s", "who");
//    py_who_value         = Py_BuildValue("s", who);
//
//    /* put all ace's fields in the dictionary */
//    /* - type */
//    PyDict_SetItem(py_ace_dict, py_type_key, py_type_value);
//    /* - whotype */
//    PyDict_SetItem(py_ace_dict, py_whotype_key, py_whotype_value);
//    /* - flags */
//    PyDict_SetItem(py_ace_dict, py_flags_key, py_flags_value);
//    /* - access_mask */
//    PyDict_SetItem(py_ace_dict, py_access_mask_key, py_access_mask_value);
//    /* - who */
//    PyDict_SetItem(py_ace_dict, py_who_key, py_who_value);
//
//    /* put the ACE PyObject in the Python list */
//    PyList_Append(py_acl_list, py_ace_dict);
//
//    nfs4_get_next_ace(&ace);
//    ace_count++;
//  }
  return py_acl_list;
}


/*********************************************************/
/* Methods table  */
/*********************************************************/
static PyMethodDef cifsaclMethods[] = {
  {"getfacl",  cifsacl_getfacl, METH_VARARGS, "get acls."},
  {NULL, NULL, 0, NULL}        /* Sentinel */
};


/*********************************************************/
/* Init  */
/*********************************************************/

PyMODINIT_FUNC
initcifsacl(void)
{
  PyObject *m;

  m = Py_InitModule("cifsacl", cifsaclMethods);
  if (m == NULL)
    return;

  CIFSaclError = PyErr_NewException("cifsacl.error", NULL, NULL);
  Py_INCREF(CIFSaclError);
  PyModule_AddObject(m, "error:", CIFSaclError);
}


