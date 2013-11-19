dnl Headers needed by wbclient.h
dnl
AC_DEFUN([AC_WBCH_COMPL],[
[
#ifdef HAVE_STDINT_H
#include <stdint.h>
#endif
]
[#ifdef HAVE_STDBOOL_H
#include <stdbool.h>
#endif
]
[#ifdef HAVE_STDIO_H
#include <stdio.h>
#endif
]
[#ifdef HAVE_STDLIB_H
#include <stdlib.h>
#endif
]
[#ifdef HAVE_ERRNO_H
#include <errno.h>
#endif
]])

dnl Check for wbclient.h header and libwbclient.so
dnl
AC_DEFUN([AC_TEST_WBCHL],[
if test $enable_cifsidmap != "no" -o $enable_cifsacl != "no"; then
	AC_CHECK_HEADERS([wbclient.h], , [
				if test "$enable_cifsidmap" = "yes"; then
					AC_MSG_ERROR([wbclient.h not found, consider installing libwbclient-devel.])
				else
					AC_MSG_WARN([wbclient.h not found, consider installing libwbclient-devel. Disabling cifs.idmap.])
					enable_cifsidmap="no"
				fi
				if test "$enable_cifsacl" = "yes"; then
					AC_MSG_ERROR([wbclient.h not found, consider installing libwbclient-devel.])
				else
					AC_MSG_WARN([wbclient.h not found, consider installing libwbclient-devel. Disabling cifsacl.])
					enable_cifsacl="no"
				fi
			], [ AC_WBCH_COMPL ])
fi

if test $enable_cifsacl != "no"; then
	AC_CHECK_HEADERS([sys/xattr.h], , [
				if test "$enable_cifsacl" = "yes"; then
					AC_MSG_ERROR([/usr/include/sys/xattr.h not found])
				else
					AC_MSG_WARN([/usr/include/sys/xattr.h not found. Disabling cifsacl.])
					enable_cifsacl="no"
				fi
			], [ ])
fi

if test $enable_cifsidmap != "no" -o $enable_cifsacl != "no"; then
	AC_CHECK_LIB([wbclient], [wbcStringToSid],
		[ WINB_LDADD='-lwbclient' ] [ AC_DEFINE(HAVE_LIBWBCLIENT, 1, ["Define var have_libwbclient"]) ], [AC_MSG_ERROR([No functioning wbclient library found!])])
	AC_SUBST(WINB_LDADD)
fi
])
