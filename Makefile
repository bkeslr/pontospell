#! /usr/bin/make -f

MINICONDA = $(HOME)/miniconda3/bin

all:	README.html test

README.html:	README.md
	pandoc --from markdown_github --to html5 --standalone --section-divs \
	  README.md --output=README.html

test:
	mypy src/pontospell tests
	pylint src/pontospell
	pylint tests --disable=duplicate-code
	pytest --verbose -v --ignore=Notes --doctest-modules

time:
	python -m timeit -s "import pontospell.chart as p" \
		"p.vertical_alignment(p.levenshtein('intention', 'execution'))"
	python -m timeit -s "import pontospell.xducer as p" \
		"p.vertical_align(p.align(p.arguments('intention', 'execution', just_one=True))[0])"

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
