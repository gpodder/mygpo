all: help

help:
	@echo 'make test            run tests and show coverage report'
	@echo 'make clean           clean up files'

test: envs/test/MEDIA_ROOT
	# assume defined media root directory, empty before running tests
	rm -rf $(shell cat envs/test/MEDIA_ROOT)
	mkdir -p $(shell cat envs/test/MEDIA_ROOT)
	envdir envs/test/ python -Wd -m coverage run ./manage.py test
	coverage report

update-po:
	envdir envs/dev/ python manage.py makemessages \
		--ignore=doc/* --ignore=envs/* --ignore=media/* --ignore=venv/* \
		--ignore=res/* --ignore=tools/* --ignore=mygpo/*/migrations/* \
		--ignore=static/*


clean:
	git clean -fX

install-deps:
	sudo apt-get install libpq-dev libjpeg-dev zlib1g-dev libwebp-dev \
		build-essential python3-dev virtualenv libffi-dev


.PHONY: all help test clean unittest coverage install-deps

