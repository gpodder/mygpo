.. gpodder.net documentation master file, created by
   sphinx-quickstart on Sat Mar  9 11:41:24 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

API Documentation
=================

This is the specification of Version 2 of the public API for the gpodder.net
Web Services.

Please consult the :doc:`integration` before integrating the gpodder.net API
in your application.

There are two different APIs for different target audiences:

* The **Simple API** targets developers who want to write quick integration
  into their existing applications
* The **Advanced API** targets developers who want tight integration into their
  applications (with more features)

The API is versioned so that changes in the major version number indicate
backwards incompatible changes. All other changes preserve backwards
compatibility. See :doc:`changes` for a list of changes. The current
version is 2.11. This versioning scheme has been introduced in `bug 1273
<https://bugs.gpodder.org/show_bug.cgi?id=1273>`_.

Contents
--------

.. toctree::
   :maxdepth: 2

   integration
   reference/index
   Libraries <http://wiki.gpodder.org/wiki/Web_Services/Libraries>
   api1
   changes
