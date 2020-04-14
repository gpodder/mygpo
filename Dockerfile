FROM python:3.6
MAINTAINER Stefan Kögl <stefan@skoegl.net>

RUN apt-get update && apt-get install -y git make

# copy source
WORKDIR /srv/mygpo

COPY makefile .

# install all packaged runtime dependencies
RUN yes | make install-deps APT=apt-get

# create log directories
RUN mkdir -p /var/log/gunicorn

COPY requirements.txt .
COPY requirements-setup.txt .

# install all runtime dependencies
RUN pip install \
    -r requirements.txt \
    -r requirements-setup.txt

# copy source
COPY . .

# Post-deployment actions
ENV SECRET_KEY temp
RUN python manage.py collectstatic --no-input
RUN python manage.py compilemessages

# set up missing environment variables
ENTRYPOINT ["/srv/mygpo/bin/docker-env.sh"]

# default launch command
CMD ["/srv/mygpo/contrib/wait-for-postgres.py", "gunicorn", "mygpo.wsgi:application", "--access-logfile", "-", "--bind=0.0.0.0:8000"]

EXPOSE 8000
