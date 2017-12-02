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
	apt-get install libpq-dev libjpeg-dev zlib1g-dev libwebp-dev \
		build-essential python3-dev make gettext virtualenv libffi-dev

docker-build:
	sudo docker build -t="mygpo/web" .

docker-run:
	sudo docker run --rm -p 8000:8000 --name web --link db:db -e SECRET_KEY=asdf mygpo/web

.PHONY: all help test clean unittest coverage install-deps

