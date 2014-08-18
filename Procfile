web: gunicorn mygpo.wsgi:application -c gunicorn.conf.py
beat: python manage.py celery beat -S djcelery.schedulers.DatabaseScheduler --pidfile /var/run/mygpo/celerybeat.pid
