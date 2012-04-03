import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"

# The maximum number of requests a worker will process before restarting.
max_requests = 100000
