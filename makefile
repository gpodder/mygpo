all: help

help:
	@echo 'make test            run tests and show coverage report'
	@echo 'make clean           clean up files'

test:
	envdir envs/dev/ coverage run ./manage.py test
	coverage report

clean:
	git clean -fX


.PHONY: all help test clean unittest coverage

