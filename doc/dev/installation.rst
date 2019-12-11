Installation
============


Dependencies
------------

When no version number is indicated, it is advisable to install the current
development version from the repository.

* Python >= 3.5
* PostgreSQL
* Redis


Basic setup
-----------

On an Debian/Ubuntu based system, you can install dependencies with

.. code-block:: bash

    make install-deps


mygpo itself can be cloned from the repository:

.. code-block:: bash

    git clone git://github.com/gpodder/mygpo.git
    cd mygpo

Now install additional dependencies locally:


.. code-block:: bash

    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip install -r requirements-dev.txt    # for local development
    pip install -r requirements-doc.txt    # for building docs
    pip install -r requirements-setup.txt  # for a productive setup
    pip install -r requirements-test.txt   # for running tests


That's it for the setup.


Configuration
-------------

Configuration of mygpo is done through environment variables. For development
purposes you can set up a directory ``envs/dev`` and create a file for each
variable that you want to set.

For a development configuration you will probably want to use the following

.. code-block:: bash

    mkdir -p envs/dev
    echo django.core.mail.backends.console.EmailBackend > envs/dev/EMAIL_BACKEND
    echo secret > envs/dev/SECRET_KEY
    echo postgres://mygpo:mygpo@localhost/mygpo > envs/dev/DATABASE_URL
    echo True > envs/dev/DEBUG
    mkdir -p /tmp/mygpo-test-media
    echo /tmp/mygpo-test-media > envs/dev/MEDIA_ROOT

On an Debian/Ubuntu based system, you can perform this configuration with

.. code-block:: bash

    make dev-config

See :ref:`configuration` for further information.


Database Initialization
-----------------------

Now to initialize the DB:

First run the commands from :ref:`db-setup`. Then

.. code-block:: bash

    cd mygpo
    envdir envs/dev python manage.py migrate

..and here we go:

.. code-block:: bash

    envdir envs/dev python manage.py runserver



Accessing the dev server from other devices
-------------------------------------------

Sometimes you might want to access the server from another machine than
localhost. In that case, you have to pass an additional argument to the
runserver command of manage.py, like this:

.. code-block:: bash

    envdir envs/dev python manage.py runserver 0.0.0.0:8000

Beware, though, that this will expose the web service to your all networks
that your machine is connected to. Apply common sense and ideally use only
on trusted networks.


Updating derived data
---------------------

Certain data in the database is only calculated when you
run special commands. This is usually done regularly on
a production server using cron. You can also run these
commands regularly on your development machine:

.. code-block:: bash

    envdir envs/dev python manage.py update-toplist
    envdir envs/dev python manage.py update-episode-toplist

    envdir envs/dev python manage.py feed-downloader
    envdir envs/dev python manage.py feed-downloader <feed-url> [...]
    envdir envs/dev python manage.py feed-downloader --max <max-updates>
    envdir envs/dev python manage.py feed-downloader --random --max <max-updates>
    envdir envs/dev python manage.py feed-downloader --toplist --max <max-updates>
    envdir envs/dev python manage.py feed-downloader --update-new --max <max-updates>

or to only do a dry run (this won't do any web requests for feeds):

.. code-block:: bash

    envdir envs/dev apython manage.py feed-downloader --list-only [other parameters]


Maintaining publisher relationships with user accounts
------------------------------------------------------

To set a user as publisher for a given feed URL, use:

.. code-block:: bash

    cd mygpo
    envdir envs/dev python manage.py make-publisher <username> <feed-url> [...]


Web-Server
----------

Django comes with a development webservice which you can run from the mygpo
directory with

.. code-block:: bash

    envdir envs/dev python manage.py runserver

If you want to run a production server, check out `Deploying Django
<https://docs.djangoproject.com/en/dev/howto/deployment/>`_.
