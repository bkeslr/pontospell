#! /usr/bin/make -f

README.html:	README.md
	pandoc --from markdown_github --to html5 --standalone --section-divs \
	  README.md --output=README.html

# Local Variables:
# mode: Makefile
# indent-tabs-mode: t
# tab-width: 2
# coding: utf-8-unix
# End:
