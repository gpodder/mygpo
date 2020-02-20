Translations
============

Translations for gpodder.net are managed on Transifex, in the
`gpodder.net project <https://www.transifex.com/gpoddernet/>`_.



Importing translations
----------------------

To import translations from transifex run the following

.. code-block:: bash

    tx pull -a
    make update


Upload new source strings
-------------------------

When changing the source code so that there are new internationalized strings
that need to be translated run the following commands to upload these to
Transifex.

.. code-block:: bash

    make update-po
    tx push -s

