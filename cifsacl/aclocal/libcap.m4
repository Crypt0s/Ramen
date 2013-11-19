dnl Checks for libcap.so
dnl
AC_DEFUN([AC_LIBCAP], [

  AC_ARG_WITH(libcap,
    [  --with-libcap    Add libcap support [default=yes, if libcap-ng not available]],,
    with_libcap=auto)

  if test "x$with_libcap" = "xno"; then
	enable_libcap="no"
  else
	dnl look for prctl
	AC_CHECK_FUNC([prctl], , )

	dnl look for the library; do not add to LIBS if found
	AC_CHECK_LIB([cap], [cap_get_proc], enable_libcap="yes", enable_libcap="no", )

	AC_CHECK_HEADERS([sys/capability.h], ,
			 [
				if test x$with_libcap = xyes; then
					AC_MSG_ERROR([libcap headers not found])
				else
					AC_MSG_WARN([libcap headers not found. mount.cifs will be built without support for dropping capabilities. Consider installing libcap-devel.])
					enable_libcap="no"
				fi
			 ])
  fi

  if test "$enable_libcap" = "yes"; then
	AC_DEFINE([HAVE_LIBCAP],[1], [Define if libcap exists])
	LIBCAP=-lcap
	AC_SUBST(LIBCAP)
  fi

])dnl
