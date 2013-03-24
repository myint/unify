check:
	pep8 unify unify.py setup.py
	pep257 unify unify.py setup.py
	pylint --report=no --include-ids=yes --disable=C0103,F0401,R0914,W0404,W0622 --rcfile=/dev/null unify.py setup.py
	python setup.py --long-description | rst2html --strict > /dev/null
	scspell unify unify.py setup.py test_unify.py README.rst

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
	@restview --long-description

register:
	@python setup.py register sdist upload
	@srm ~/.pypirc
