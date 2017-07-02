FROM ubuntu:14.04
MAINTAINER Stefan Kögl <stefan@skoegl.net>

# use bash instead of built-in sh, because it does not support "source" during build
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

RUN apt-get update

# install Docker dependencies
RUN apt-get install -y git virtualenv

# install all packaged runtime dependencies
RUN yes | make install-deps

# create log directories
RUN mkdir -p /var/log/gunicorn

# copy source
COPY . /srv/mygpo
WORKDIR /srv/mygpo

# run everything in a virtualenv
RUN virtualenv venv
RUN source venv/bin/activate

# install all runtime dependencies
RUN pip install \
    -r /srv/mygpo/requirements.txt \
    -r /srv/mygpo/requirements-setup.txt

# set up missing environment variables
ENTRYPOINT ["/srv/mygpo/bin/docker-env.sh"]

# default launch command
CMD ["gunicorn", "mygpo.wsgi:application", "--access-logfile", "-"]

# HTTP port
EXPOSE 8000
