# import multiprocessing
import os

bind = "unix:/tmp/mygpo.sock"
#workers = multiprocessing.cpu_count()
workers = 3

# The maximum number of requests a worker will process before restarting.
# max_requests = 1000

log_dir = os.getenv("LOGGING_DIR_GUNICRON", "/var/log/gunicorn/")
errorlog = log_dir + "error.log"
accesslog = log_dir + "access.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(T)s "%(f)s" "%(a)s"'

timeout = 120
graceful_timeout = 60


def get_bool(name, default):
    return os.getenv(name, str(default)).lower() == "true"


def _post_fork_handler(server, worker):
    patch_psycopg()
    worker.log.info("Made Psycopg2 Green")


# check if we want to use gevent
_USE_GEVENT = get_bool("USE_GEVENT", False)


try:
    # check if we *can* use gevent
    from psycogreen.gevent import patch_psycopg
except ImportError:
    _USE_GEVENT = False


if _USE_GEVENT:
    # Active gevent-related settings

    workers = 9
    worker_connections = 100
    worker_class = "gevent"

    # activate the handler
    post_fork = _post_fork_handler
else:
    thread = 3
    worker_class = "gthread"
