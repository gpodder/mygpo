.. _jupyter-notebook:

Jupyter Notebook
================

You can use `Jupyter Notebooks <http://jupyter.org/>`_ during development for
exploring data and prototyping methods.

To do so, follow these steps

* Make sure you have all requirements from ``requirements-dev.txt`` installed.

* Run ``make notebook``, which will start the notebook and open it in the
  browser .

* Navigate to the directory ``notebooks`` (listed in `.gitignore`) and create
  a new notebook.

* Use the following code in the first cell to setup your environment

  .. code-block:: python

     MYPROJECT = '/path/to/mygpo'
     import os, sys
     sys.path.insert(0, MYPROJECT)
     os.environ.setdefault("DJANGO_SETTINGS_MODULE", "local_settings.py")
     import django
     django.setup()
