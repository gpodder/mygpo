all: help

help:
	@echo 'make test            synchronize DB and run local webserver'
	@echo 'make clean           clean up files'
	@echo 'make unittest        run unittests'

test:
	python manage.py syncdb
	python manage.py runserver

unittest:
	python manage.py test

coverage:
	coverage run --omit="/usr/*" manage.py test
	coverage report -m
	rm .coverage

clean:
	find -name "*.pyc" -exec rm '{}' \;

docker-build:
	sudo docker build -t="mygpo/web" .

docker-run:
	sudo docker run --rm -p 8000:8000 --name web --link db:db -e SECRET_KEY=asdf mygpo/web

.PHONY: all help test clean unittest coverage

