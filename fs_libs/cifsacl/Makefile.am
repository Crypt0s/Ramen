AM_CFLAGS = -Wall -Wextra
ACLOCAL_AMFLAGS = -I aclocal

root_sbindir = "/sbin"
root_sbin_PROGRAMS = mount.cifs
mount_cifs_SOURCES = mount.cifs.c mtab.c resolve_host.c util.c
mount_cifs_LDADD = $(LIBCAP) $(CAPNG_LDADD)

man_MANS = mount.cifs.8

bin_PROGRAMS =
sbin_PROGRAMS =
clean-local: clean-local-upcall clean-local-idmap clean-local-aclprogs

if CONFIG_CIFSUPCALL
sbin_PROGRAMS += cifs.upcall
cifs_upcall_SOURCES = cifs.upcall.c data_blob.c asn1.c spnego.c
cifs_upcall_LDADD = -ltalloc -lkeyutils $(KRB5_LDADD)
man_MANS += cifs.upcall.8

#
# Fix the pathnames in manpages. To prevent @label@ being replaced by m4, we
# need to obfuscate the LHS of the regex (hence the trivial one character set).
#
cifs.upcall.8: cifs.upcall.8.in
	$(SED) 's,[@]sbindir@,$(sbindir),' $(srcdir)/$@.in > $@-t && mv $@-t $@
endif

clean-local-upcall:
if CONFIG_CIFSUPCALL
	rm -f cifs.upcall.8 cifs.upcall.8-t
endif

if CONFIG_CIFSCREDS
bin_PROGRAMS += cifscreds
cifscreds_SOURCES = cifscreds.c resolve_host.c util.c
cifscreds_LDADD = -lkeyutils
endif

if CONFIG_CIFSIDMAP
sbin_PROGRAMS += cifs.idmap
cifs_idmap_SOURCES = cifs.idmap.c
cifs_idmap_LDADD = -lkeyutils $(WINB_LDADD)
man_MANS += cifs.idmap.8

cifs.idmap.8: cifs.idmap.8.in
	$(SED) 's,[@]sbindir@,$(sbindir),' $(srcdir)/$@.in > $@-t && mv $@-t $@
endif

clean-local-idmap:
if CONFIG_CIFSIDMAP
	rm -f cifs.idmap.8 cifs.idmap.8-t
endif

if CONFIG_CIFSACL
bin_PROGRAMS += getcifsacl
getcifsacl_SOURCES = getcifsacl.c
getcifsacl_LDADD = -lkeyutils $(WINB_LDADD)
man_MANS += getcifsacl.1

bin_PROGRAMS += setcifsacl
setcifsacl_SOURCES = setcifsacl.c
setcifsacl_LDADD = -lkeyutils $(WINB_LDADD)
man_MANS += setcifsacl.1

endif

clean-local-aclprogs:
if CONFIG_CIFSACL
	rm -f getcifsacl.8 getcifsacl.8-t setcifsacl.8 setcifsacl.8-t
endif

SUBDIRS = contrib
