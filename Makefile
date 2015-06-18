.PHONY: doc test
PROG=scriptform

fake:
	# NOOP

install:
	cp src/scriptform.py /usr/bin/scriptform

uninstall:
	rm /usr/bin/scriptform

release: release_src release_deb release_rpm

doc:
	markdown_py doc/MANUAL.md > doc/MANUAL.html
	markdown_py README.md > README.html

release_src: doc
	@echo "Making release for version $(REL_VERSION)"

	@if [ -z "$(REL_VERSION)" ]; then echo "REL_VERSION required"; exit 1; fi

	# Prepare source
	rm -rf $(PROG)-$(REL_VERSION)
	mkdir $(PROG)-$(REL_VERSION)
	cp src/scriptform.py $(PROG)-$(REL_VERSION)/scriptform
	cp src/daemon.py $(PROG)-$(REL_VERSION)/
	cp src/formconfig.py $(PROG)-$(REL_VERSION)/
	cp src/formdefinition.py $(PROG)-$(REL_VERSION)/
	cp src/formrender.py $(PROG)-$(REL_VERSION)/
	cp src/webapp.py $(PROG)-$(REL_VERSION)/
	cp LICENSE $(PROG)-$(REL_VERSION)/
	cp README.md $(PROG)-$(REL_VERSION)/
	cp contrib/release_Makefile $(PROG)-$(REL_VERSION)/Makefile
	cp doc/MANUAL.html $(PROG)-$(REL_VERSION)/MANUAL.html

	# Bump version numbers
	find $(PROG)-$(REL_VERSION)/ -type f -print0 | xargs -0 sed -i "s/%%VERSION%%/$(REL_VERSION)/g" 

	# Create archives
	zip -r $(PROG)-$(REL_VERSION).zip $(PROG)-$(REL_VERSION)
	tar -vczf $(PROG)-$(REL_VERSION).tar.gz  $(PROG)-$(REL_VERSION)

release_deb: doc
	@if [ -z "$(REL_VERSION)" ]; then echo "REL_VERSION required"; exit 1; fi

	mkdir -p rel_deb/usr/bin
	mkdir -p rel_deb/usr/lib/scriptform
	mkdir -p rel_deb/usr/share/doc/$(PROG)
	mkdir -p rel_deb/usr/share/man/man1

	# Copy the source to the release directory structure.
	cp LICENSE rel_deb/usr/share/doc/$(PROG)
	cp README.md rel_deb/usr/share/doc/$(PROG)
	cp doc/MANUAL.md rel_deb/usr/share/doc/$(PROG)
	cp README.html $(PROG)-$(REL_VERSION)/README.html
	cp doc/MANUAL.html $(PROG)-$(REL_VERSION)/MANUAL.html
	cp src/scriptform.py rel_deb/usr/lib/scriptform/
	cp src/daemon.py rel_deb/usr/lib/scriptform/
	cp src/formconfig.py rel_deb/usr/lib/scriptform/
	cp src/formdefinition.py rel_deb/usr/lib/scriptform/
	cp src/formrender.py rel_deb/usr/lib/scriptform/
	cp src/webapp.py rel_deb/usr/lib/scriptform/
	ln -s /usr/lib/scriptform/scriptform.py rel_deb/usr/bin/scriptform

	cp contrib/scriptform.init.d_debian rel_deb/usr/share/doc/$(PROG)
	cp contrib/scriptform.init.d_redhat rel_deb/usr/share/doc/$(PROG)
	cp -ar contrib/debian/DEBIAN rel_deb/

	# Bump version numbers
	find rel_deb/ -type f -print0 | xargs -0 sed -i "s/%%VERSION%%/$(REL_VERSION)/g" 

	# Create debian pacakge
	fakeroot dpkg-deb --build rel_deb > /dev/null
	mv rel_deb.deb $(PROG)-$(REL_VERSION).deb

	# Cleanup
	rm -rf rel_deb

release_rpm: release_deb
	alien -r scriptform-$(REL_VERSION).deb

clean:
	rm -rf *.tar.gz
	rm -rf *.zip
	rm -rf *.deb
	rm -rf rel_deb
	rm -rf scriptform-*
	rm -rf doc/manual.html
	rm -rf doc/MANUAL.html
	rm -rf examples/megacorp_acc/megacorp.db
	rm -rf examples/megacorp_acc/.coverage
	rm -rf examples/megacorp_acc/htmlcov
	find ./ -name "*.log" -delete
	find ./ -name "*.pyc" -delete
	rm -rf $(PROG)-$(REL_VERSION)


test:
	@echo "\nTESTS\n"
	cd test && python ./test.py
	@echo "\nFLAKE8\n"
	cd src && flake8 *.py || true
	@echo "\nPYLINT\n"
	cd src && pylint --reports=n -dR -dW0142 *.py || true
