#! /usr/bin/make -f

MINICONDA = $(HOME)/miniconda3/bin

all:	README.html test

README.html:	README.md
	pandoc --from markdown_github --to html5 --standalone --section-divs \
	  README.md --output=README.html

test:
	mypy src/pontospell
	pylint src/pontospell
	pylint tests
	pytest --verbose -v --ignore=Notes --doctest-modules
	#pytest --verbose --doctest-modules -r chars

create-env:
	$(MINICONDA)/conda install conda-build
	$(MINICONDA)/conda-env create --file=environment.yml
	$(MINICONDA)/conda-develop --name=pontospell src

# To use the `pontospell` environment:
# source activate pontospell

update-env:
	$(MINICONDA)/conda env update --file=environment.yml

remove-env:
	$(MINICONDA)/conda env remove --name=pontospell


# Local Variables:
# mode: Makefile
# indent-tabs-mode: t
# tab-width: 2
# coding: utf-8-unix
# End:
