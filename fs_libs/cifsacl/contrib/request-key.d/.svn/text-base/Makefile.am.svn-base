noinst_DATA = cifs.idmap.conf cifs.spnego.conf
cifs.idmap.conf: cifs.idmap.conf.in
	$(SED) 's,[@]sbindir@,$(sbindir),' $(srcdir)/$@.in > $@-t && mv $@-t $@

cifs.spnego.conf: cifs.spnego.conf.in
	$(SED) 's,[@]sbindir@,$(sbindir),' $(srcdir)/$@.in > $@-t && mv $@-t $@

clean-local:
	rm -f cifs.idmap.conf cifs.spnego.conf
