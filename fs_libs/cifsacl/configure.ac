#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_INIT([cifs-utils], [5.2.1], [cifs-utils@samba.org], [cifs-utils], [http://linux-cifs.samba.org/cifs-utils/])
AC_CONFIG_SRCDIR([replace.h])
AC_CONFIG_HEADERS([config.h])
AC_CONFIG_FILES([Makefile contrib/Makefile contrib/request-key.d/Makefile])
AC_CONFIG_MACRO_DIR(aclocal)

AM_INIT_AUTOMAKE

# "with" options
AC_ARG_ENABLE(cifsupcall,
	[AC_HELP_STRING([--enable-cifsupcall],
			[Create cifs.upcall binary @<:@default=yes@:>@])],
	enable_cifsupcall=$enableval,
	enable_cifsupcall="maybe")

AC_ARG_ENABLE(cifscreds,
	[AC_HELP_STRING([--enable-cifscreds],
			[Create cifscreds utility @<:@default=no@:>@])],
	enable_cifscreds=$enableval,
	enable_cifscreds="no")

AC_ARG_ENABLE(cifsidmap,
	[AC_HELP_STRING([--enable-cifsidmap],
			[Create cifs.idmap binary @<:@default=yes@:>@])],
	enable_cifsidmap=$enableval,
	enable_cifsidmap="maybe")

AC_ARG_ENABLE(cifsacl,
	[AC_HELP_STRING([--enable-cifsacl],
			[Create get/set cifsacl binary @<:@default=yes@:>@])],
	enable_cifsacl=$enableval,
	enable_cifsacl="maybe")

# Checks for programs.
AC_PROG_CC
AC_PROG_SED
AC_GNU_SOURCE

# Checks for typedefs, structures, and compiler characteristics.
AC_HEADER_STDBOOL
AC_TYPE_UID_T
AC_TYPE_OFF_T
AC_TYPE_PID_T
AC_TYPE_SIZE_T
AC_CHECK_TYPES([ptrdiff_t, ssize_t, uint32_t, uint8_t])

# Checks for library functions.
AC_FUNC_GETMNTENT
AC_FUNC_LSTAT_FOLLOWS_SLASHED_SYMLINK
AC_FUNC_MALLOC
AC_FUNC_REALLOC
AC_FUNC_STRNLEN

# check for required functions
AC_CHECK_FUNCS([alarm atexit endpwent getmntent getpass gettimeofday inet_ntop memset realpath setenv strchr strcmp strdup strerror strncasecmp strndup strpbrk strrchr strstr strtol strtoul tolower uname], , [AC_MSG_ERROR([necessary functions(s) not found])])

AC_CHECK_FUNCS(clock_gettime, [], [
  AC_CHECK_LIB(rt, clock_gettime, [
      AC_DEFINE(HAVE_CLOCK_GETTIME, 1)
	AC_DEFINE(HAVE_CLOCK_GETTIME,1,
		[Whether the clock_gettime func is there])
      LIBS="$LIBS -lrt"
        ])
  ])

# Checks for header files.
AC_CHECK_HEADERS([arpa/inet.h ctype.h fcntl.h inttypes.h limits.h mntent.h netdb.h stddef.h stdint.h stdbool.h stdlib.h stdio.h errno.h string.h strings.h sys/mount.h sys/param.h sys/socket.h sys/time.h syslog.h unistd.h], , [AC_MSG_ERROR([necessary header(s) not found])])

if test $enable_cifsupcall != "no"; then
	AC_CHECK_HEADERS([krb5.h krb5/krb5.h])
	if test x$ac_cv_header_krb5_krb5_h != xyes ; then
		if test x$ac_cv_header_krb5_h != xyes ; then
			if test "$enable_cifsupcall" = "yes"; then
				AC_MSG_ERROR([krb5.h not found, consider installing krb5-libs-devel.])
			else
				AC_MSG_WARN([krb5.h not found, consider installing krb5-libs-devel. Disabling cifs.upcall.])
				enable_cifsupcall="no"
			fi
		fi
	fi
fi
if test $enable_cifsupcall != "no"; then
	if test x$ac_cv_header_krb5_krb5_h = xyes ; then
		krb5_include="#include <krb5/krb5.h>"
	fi
	if test x$ac_cv_header_krb5_h = xyes ; then
		krb5_include="#include <krb5.h>"
	fi

	AC_CACHE_CHECK([for keyvalue in krb5_keyblock],
		[ac_cv_have_krb5_keyblock_keyvalue],[
			AC_TRY_COMPILE([$krb5_include],
			[krb5_keyblock key; key.keyvalue.data = NULL;],
			ac_cv_have_krb5_keyblock_keyvalue=yes,
			ac_cv_have_krb5_keyblock_keyvalue=no)])
	if test x"$ac_cv_have_krb5_keyblock_keyvalue" = x"yes" ; then
		AC_DEFINE(HAVE_KRB5_KEYBLOCK_KEYVALUE,1,
			[Whether the krb5_keyblock struct has a keyvalue property])
	fi
fi
if test $enable_cifsupcall != "no"; then
	AC_CHECK_HEADERS([talloc.h], , [
				if test "$enable_cifsupcall" = "yes"; then
					AC_MSG_ERROR([talloc.h not found, consider installing libtalloc-devel.])
				else
					AC_MSG_WARN([talloc.h not found, consider installing libtalloc-devel. Disabling cifs.upcall.])
					enable_cifsupcall="no"
				fi
			])
fi
if test $enable_cifsupcall != "no" -o $enable_cifsidmap != "no"; then
	AC_CHECK_HEADERS([keyutils.h], , [
				if test "$enable_cifsupcall" = "yes"; then
					AC_MSG_ERROR([keyutils.h not found, consider installing keyutils-libs-devel.])
				else
					AC_MSG_WARN([keyutils.h not found, consider installing keyutils-libs-devel. Disabling cifs.upcall.])
					enable_cifsupcall="no"
				fi
				if test "$enable_cifsidmap" = "yes"; then
					AC_MSG_ERROR([keyutils.h not found, consider installing keyutils-libs-devel.])
				else
					AC_MSG_WARN([keyutils.h not found, consider installing keyutils-libs-devel. Disabling cifs.idmap.])
					enable_cifsidmap="no"
				fi
			])
fi
if test $enable_cifsacl != "no"; then
	AC_CHECK_HEADERS([wbclient.h], , [
				if test "$enable_cifsacl" = "yes"; then
					AC_MSG_ERROR([wbclient.h not found, consider installing libwbclient-devel.])
				else
					AC_MSG_WARN([wbclient.h not found, consider installing libwbclient-devel. Disabling getcifsacl.])
					enable_cifsacl="no"
				fi
			],
			[AC_INCLUDES_DEFAULT]
			[#ifdef HAVE_STDBOOL_H
			    #include <stdbool.h>
			    #endif
			])
fi
if test $enable_cifsupcall != "no"; then
	AC_CHECK_LIB([krb5], [krb5_init_context],
			[ KRB5_LDADD='-lkrb5' ],
			AC_MSG_ERROR([no functioning krb5 library found!]))
	AC_SUBST(KRB5_LDADD)
fi

# checks for wbclient.h and libwbclient.so library
AC_TEST_WBCHL

if test $enable_cifscreds = "yes"; then
	AC_CHECK_HEADERS([keyutils.h], , [AC_MSG_ERROR([keyutils.h not found, consider installing keyutils-libs-devel.])])
fi


# ugly, but I'm not sure how to check for functions in a library that's not in $LIBS
cu_saved_libs=$LIBS
LIBS="$LIBS $KRB5_LDADD"

# determine whether we can use MIT's new 'krb5_auth_con_getsendsubkey' to extract the signing key
if test $enable_cifsupcall != "no"; then
	AC_CHECK_FUNCS([krb5_auth_con_getsendsubkey])
fi

# non-critical functions (we have workarounds for these)
if test $enable_cifsupcall != "no"; then
	AC_CHECK_FUNCS([krb5_principal_get_realm krb5_free_unparsed_name])
	AC_CHECK_FUNCS([krb5_auth_con_setaddrs krb5_auth_con_set_req_cksumtype])
fi

LIBS=$cu_saved_libs

AM_CONDITIONAL(CONFIG_CIFSUPCALL, [test "$enable_cifsupcall" != "no"])
AM_CONDITIONAL(CONFIG_CIFSCREDS, [test "$enable_cifscreds" = "yes"])
AM_CONDITIONAL(CONFIG_CIFSIDMAP, [test "$enable_cifsidmap" != "no"])
AM_CONDITIONAL(CONFIG_CIFSACL, [test "$enable_cifsacl" != "no"])

LIBCAP_NG_PATH

if test "x$CAPNG_LDADD" = "x"; then
	AC_LIBCAP
fi
AC_OUTPUT
