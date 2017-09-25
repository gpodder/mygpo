web: gunicorn mygpo.wsgi:application -c gunicorn.conf.py
beat: python manage.py celery beat -S django --pidfile /var/run/mygpo/celerybeat.pid
