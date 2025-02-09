FROM python:3.9-buster as base

EXPOSE 8000
STOPSIGNAL SIGTERM
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# ENV DEBUG 1

RUN apt-get update
RUN apt-get install -y libpq-dev libjpeg-dev zlib1g-dev libwebp-dev libffi-dev

# copy source and install dependencies
RUN mkdir -p /app

WORKDIR /app

COPY . /app
RUN python -m pip install -r requirements.txt

FROM base as dev

RUN python -m pip install -r requirements-dev.txt
RUN make dev-config

CMD ["envdir", "envs/dev", "python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM dev as test

RUN python -m pip install -r requirements-test.txt

CMD ["make", "test"]

FROM base as production

RUN python -m pip install -r requirements-kubernetes.txt

CMD ["python", "-m", "kubernetes_wsgi", "mygpo.wsgi", "--port", "8000"]
