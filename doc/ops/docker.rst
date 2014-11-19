Using Docker
============

mygpo can be run using `Docker <https://docker.com/>`_.


Database
--------

The image requires a PostgreSQL server, specified either via

* a `linked container <https://docs.docker.com/userguide/dockerlinks/>`_
  called ``db`` containing a server with a database called ``mygpo``, a user
  called ``mygpo`` with a password ``mygpo``.
* A ``DATABASE_URL`` environment variable (eg
  ``postgres://USER:PASSWORD@HOST:PORT/NAME``)

Using a PostgreSQL Docker container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Start a container using the `official PostgreSQL image <https://registry.hub.docker.com/_/postgres/>`_. ::

    docker run --name db -d postgres

Create the schema and a corresponding user ::

    docker exec -it db psql -U postgres

And enter the following commands (change passwords as required)

.. literalinclude:: ../../contrib/init-db.sql
    :language: sql
    :linenos:

Initialize the tables. This needs needs to be run for every update. ::

    sudo docker run --rm --link db:db -e SECRET_KEY=asdf mygpo/web python manage.py migrate


Elasticsearch
-------------


Redis
-----


Web Frontend
------------

The image exposes the web interface on port 8000.


Celery Worker
-------------


Celery Heartbeat
----------------


