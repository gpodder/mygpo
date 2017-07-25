CREATE USER mygpo WITH PASSWORD 'mygpo';
ALTER USER mygpo CREATEDB;  -- required for creating test database
CREATE DATABASE mygpo;
CREATE DATABASE test_mygpo;
GRANT ALL PRIVILEGES ON DATABASE mygpo to mygpo;
GRANT ALL PRIVILEGES ON DATABASE test_mygpo to mygpo;
ALTER DATABASE mygpo OWNER TO mygpo;
ALTER DATABASE test_mygpo OWNER TO mygpo;
ALTER ROLE mygpo SET statement_timeout = 5000;
