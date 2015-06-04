all: help

help:
	@echo 'make test            run tests and show coverage report'
	@echo 'make clean           clean up files'

test:
	envdir envs/dev/ coverage run --branch --source=mygpo ./manage.py test
	coverage report --show-missing

clean:
	find -name "*.pyc" -exec rm '{}' \;


.PHONY: all help test clean unittest coverage

