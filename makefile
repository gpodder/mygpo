all: help

help:
	@echo 'make test            run tests and show coverage report'
	@echo 'make clean           clean up files'

dev-config:
	mkdir -p envs/dev
	echo django.core.mail.backends.console.EmailBackend > envs/dev/EMAIL_BACKEND
	echo secret > envs/dev/SECRET_KEY
	echo postgres://mygpo:mygpo@localhost/mygpo > envs/dev/DATABASE_URL
	echo True > envs/dev/DEBUG

test: envs/dev/MEDIA_ROOT
	# assume defined media root directory, empty before running tests
	rm -rf $(shell cat envs/dev/MEDIA_ROOT)
	mkdir -p $(shell cat envs/dev/MEDIA_ROOT)
	envdir envs/dev/ pytest --cov=mygpo/ --cov-branch
	coverage report --show-missing

update-po:
	envdir envs/dev/ python manage.py makemessages \
		--ignore=doc/* --ignore=envs/* --ignore=media/* --ignore=venv/* \
		--ignore=res/* --ignore=tools/* --ignore=mygpo/*/migrations/* \
		--ignore=static/*

compilemessages:
	envdir envs/dev/ python manage.py compilemessages

notebook:
	envdir envs/dev/ python manage.py shell_plus --notebook

clean:
	git clean -fX

install-deps:
	sudo apt-get install libpq-dev libjpeg-dev zlib1g-dev libwebp-dev \
		build-essential python3-dev virtualenv libffi-dev

format-code:
	black --target-version py36 --skip-string-normalization mygpo/

check-code-format:
	black --check --target-version py36 --skip-string-normalization mygpo/


.PHONY: all help test clean unittest coverage install-deps format-code

