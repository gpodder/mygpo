Python 3 Dependencies
=====================

This list tracks the Python-3-readiness of all dependencies

OK
--
* feedparser # according to http://python3wos.appspot.com/
* python-dateutil # according to http://python3wos.appspot.com/
* Django # according to http://python3wos.appspot.com/
* simplejson # according to http://python3wos.appspot.com/
* celery # according to http://python3wos.appspot.com/
* markdown2 # according to README.md
* pillow # according to http://python3wos.appspot.com/

Not OK
------
* restkit # https://github.com/benoitc/restkit/tree/py3_2
* couchdbkit
* Babel # used only in one place, could maybe be removed as a (hard) dependency

Unknown
-------
* mygpo-feedservice
* celery-redis
