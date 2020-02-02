import multiprocessing

bind = "unix:/tmp/mygpo.sock"
workers = multiprocessing.cpu_count()

# The maximum number of requests a worker will process before restarting.
# max_requests = 1000

errorlog='/var/log/gunicorn/error.log'
accesslog='/var/log/gunicorn/access.log'
loglevel='info'

timeout = 120
graceful_timeout = 60


def get_bool(name, default):
    return os.getenv(name, str(default)).lower() == 'true'


def _post_fork_handler(server, worker):
    patch_psycopg()
    worker.log.info("Made Psycopg2 Green")


# check if we want to use gevent
_USE_GEVENT = get_bool('USE_GEVENT', False)


try:
    # check f we *can* use gevent
    from psycogreen.gevent import patch_psycopg
except ImportError:
    _USE_GEVENT = False


if _USE_GEVENT:
    # Active gevent-related settings

    worker_connections = 100
    worker_class = 'gevent'

    # activate the handler
    post_fork = _post_fork_handler
