import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1

# The maximum number of requests a worker will process before restarting.
max_requests = 1000

errorlog='/var/log/gunicorn/error.log'
accesslog='/var/log/gunicorn/access.log'
loglevel='info'

timeout = 120
graceful_timeout = 60
