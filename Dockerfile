FROM python:3
MAINTAINER Stefan Kögl <stefan@skoegl.net>

# install all packaged dependencies
RUN apt-get update && apt-get install -y \
    git \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libwebp-dev

# create log directories
RUN mkdir -p /var/log/gunicorn

WORKDIR /srv/mygpo

COPY requirements.txt .
COPY requirements-setup.txt .

# install all runtime dependencies
RUN pip install \
    -r requirements.txt \
    -r requirements-setup.txt

# copy source
COPY . .

# set up missing environment variables
ENTRYPOINT ["/srv/mygpo/bin/docker-env.sh"]

# default launch command
CMD ["gunicorn", "mygpo.wsgi:application", "--access-logfile", "-"]
