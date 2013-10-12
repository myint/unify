check:
	pep8 unify.py setup.py
	pep257 unify.py setup.py
	pylint \
		--reports=no \
		--disable=invalid-name \
		--rcfile=/dev/null \
		unify.py setup.py
	python setup.py --long-description | rst2html --strict > /dev/null
	scspell unify.py setup.py test_unify.py README.rst

coverage:
	@rm -f .coverage
	@coverage run test_unify.py
	@coverage report
	@coverage html
	@rm -f .coverage
	@python -m webbrowser -n "file://${PWD}/htmlcov/index.html"

mutant:
	@mut.py -t unify -u test_unify -mc

readme:
	@restview --long-description --strict
