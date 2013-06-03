import multiprocessing

bind='unix:/tmp/mygpo.sock'
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"

# The maximum number of requests a worker will process before restarting.
max_requests = 1000

errorlog='/var/log/gunicorn/error.log'
accesslog='/var/log/gunicorn/access.log'
loglevel='info'

timeout = 120
graceful_timeout = 60
