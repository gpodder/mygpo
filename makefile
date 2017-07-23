all: help

help:
	@echo 'make test            run tests and show coverage report'
	@echo 'make clean           clean up files'

test:
	envdir envs/dev/ coverage run ./manage.py test
	coverage report

update-po:
	envdir envs/dev/ python manage.py makemessages \
		--ignore=doc/* --ignore=envs/* --ignore=htdocs/* --ignore=venv/* \
		--ignore=res/* --ignore=tools/* --ignore=mygpo/*/migrations/*


clean:
	git clean -fX

install-deps:
	sudo apt-get install libpq-dev libjpeg-dev zlib1g-dev libwebp-dev \
		build-essential python3-dev

docker-build:
	sudo docker build -t="mygpo/web" .

docker-run:
	sudo docker run --rm -p 8000:8000 --name web --link db:db -e SECRET_KEY=asdf mygpo/web

.PHONY: all help test clean unittest coverage install-deps

