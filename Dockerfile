FROM ubuntu:latest
MAINTAINER Stefan Kögl <stefan@skoegl.net>

# use bash instead of built-in sh, because it does not support "source" during build
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

RUN apt-get update

# install Docker dependencies
RUN apt-get install -y git virtualenv make

# copy source
COPY . /srv/mygpo
WORKDIR /srv/mygpo

# install all packaged runtime dependencies
RUN yes | make install-deps

# create log directories
RUN mkdir -p /var/log/gunicorn

# run everything in a virtualenv
RUN virtualenv -p `which python3` venv
RUN source venv/bin/activate

# install all runtime dependencies
RUN venv/bin/pip install \
    -r /srv/mygpo/requirements.txt \
    -r /srv/mygpo/requirements-setup.txt

# set up missing environment variables
ENTRYPOINT ["/srv/mygpo/bin/docker-env.sh"]

# default launch command
CMD ["gunicorn", "mygpo.wsgi:application", "--access-logfile", "-"]

# HTTP port
EXPOSE 8000
