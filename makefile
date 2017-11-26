all: help

help:
	@echo 'make test            run tests and show coverage report'
	@echo 'make clean           clean up files'

test:
	envdir envs/dev/ pytest --cov=mygpo/ --cov-branch
	coverage report --show-missing

update-po:
	envdir envs/dev/ python manage.py makemessages \
		--ignore=doc/* --ignore=envs/* --ignore=htdocs/* --ignore=venv/* \
		--ignore=res/* --ignore=tools/* --ignore=mygpo/*/migrations/*

notebook:
	envdir envs/dev/ python manage.py shell_plus --notebook

clean:
	git clean -fX

install-deps:
	sudo apt-get install libpq-dev libjpeg-dev zlib1g-dev libwebp-dev \
		build-essential python3-dev virtualenv libffi-dev


.PHONY: all help test clean unittest coverage install-deps

