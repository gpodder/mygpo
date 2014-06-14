PostgreSQL Setup
================

Use the following to set up a local PostgreSQL.

.. code-block:: sql

    CREATE USER mygpo WITH PASSWORD 'mygpo';
    CREATE DATABASE mygpo;
    CREATE DATABASE test_mygpo;
    GRANT ALL PRIVILEGES ON DATABASE mygpo to mygpo;
    GRANT ALL PRIVILEGES ON DATABASE test_mygpo to mygpo;
    ALTER DATABASE mygpo OWNER TO mygpo;
    ALTER DATABASE test_mygpo OWNER TO mygpo;
