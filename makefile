all: help

help:
	@echo 'make test            run tests and show coverage report'
	@echo 'make clean           clean up files'

test:
	envdir envs/dev/ coverage run ./manage.py test
	coverage report

clean:
	git clean -fX

install-deps:
	sudo apt-get install libpq-dev libjpeg-dev zlib1g-dev libwebp-dev \
		build-essential python3-dev virtualenv


.PHONY: all help test clean unittest coverage install-deps

