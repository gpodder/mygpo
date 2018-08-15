all: help

help:
	@echo 'make test            run tests and show coverage report'
	@echo 'make clean           clean up files'

dev-config:
	mkdir -p envs/local
	echo django.core.mail.backends.console.EmailBackend > envs/local/EMAIL_BACKEND
	echo secret > envs/local/SECRET_KEY
	echo postgres://mygpo:mygpo@localhost/mygpo > envs/local/DATABASE_URL
	echo True > envs/local/DEBUG

test: envs/test/MEDIA_ROOT
	# assume defined media root directory, empty before running tests
	rm -rf $(shell cat envs/test/MEDIA_ROOT)
	mkdir -p $(shell cat envs/test/MEDIA_ROOT)
	envdir envs/dev/ pytest --cov=mygpo/ --cov-branch
	coverage report --show-missing

update-po:
	envdir envs/dev/ python manage.py makemessages \
		--ignore=doc/* --ignore=envs/* --ignore=media/* --ignore=venv/* \
		--ignore=res/* --ignore=tools/* --ignore=mygpo/*/migrations/* \
		--ignore=static/*

notebook:
	envdir envs/dev/ python manage.py shell_plus --notebook

clean:
	git clean -fX

install-deps:
	apt-get install libpq-dev libjpeg-dev zlib1g-dev libwebp-dev \
		build-essential python3-dev make gettext virtualenv libffi-dev

docker-build:
	sudo docker build -t="mygpo/web" .

docker-run:
	sudo docker run --rm -p 8000:8000 --name web --link db:db -e SECRET_KEY=asdf mygpo/web

.PHONY: all help test clean unittest coverage install-deps

