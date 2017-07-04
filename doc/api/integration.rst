.. _integration-guide:

Integration Guide
=================

This guide describes how the gpodder.net API can be integrated in podcast
applications. It describes good practice and points out caveats.


General
-------

* The `Mailing List <http://wiki.gpodder.org/wiki/Mailing_List>`_ is the right
  place to ask questions

* Consult the :ref:`api-reference` for available functionality.

* Add your client to `the clients list
  <http://wiki.gpodder.org/wiki/Web_Services/Clients>`_ when you're ready

* Please use the name *gpodder.net* (all lowercase, .net suffix) to refer to
  the webservice. *gPodder* (uppercase P, no suffix) refers to the `client
  application <http://gpodder.org/>`_.


Implementation
--------------

* If possible/available use an `existing library
  <http://wiki.gpodder.org/wiki/Web_Services/Libraries>`_.

* If you have to implement your own client, please consider releasing it as a
  library.

* Try to keep the requests to the API to a sensible limit. There are no hard
  limit, please judge for yourself what is necessary in your case. Please ask
  on the mailing list if unsure. Your client might get blocked if it
  misbehaves.

* Your client should send a useful User-Agent header. We might block clients
  with generic/missing User-Agent headers.


Integration
-----------

The following contains useful information for integrating gpodder.net into a
podcast application.


.. _device-integration:

Device
^^^^^^

Many API endpoints refer to a *device*. A device is an instance of a client
accessing the API. The ID of a device must be unique per user. Therefore
clients should generate a device ID such that it is unique for the user, even
he uses the same application on multiple devices. A common strategy is to
include the applications name and the hostname

A user might use several clients for playing podcasts, which could generate
device Id like the following

* gPodder on his N9 (*gpodder-n9*)
* gPodder on his notebook (*gpodder-netbook*)
* Amarok on his PC (*amarok-mypc*)
* a web based player (*mywebservice-myusername*)

When a previously unknown device Id is used in some API request, a device is
automatically created. Refer to the :doc:`reference/devices` on how to provide
some information about the device. Users can manage their devices `online
<https://gpodder.net/devices>`_.


Podcast Directory
^^^^^^^^^^^^^^^^^

The most basic *passive* integration with gpodder.net is to access some of its
public data. Refer to the :doc:`reference/directory` for available endpoints.


Subscription Management
^^^^^^^^^^^^^^^^^^^^^^^

The most common form of *active* integration is subscription management.
Clients can upload the podcast subscriptions using their device Id and receive
subscription changes (for their device) that were made online. Refer to the
:doc:`reference/subscriptions` for additional information.


Episode Actions Synchronization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Clients can upload and download certain actions (episode downloaded, played,
deleted) to/from gpodder.net. This gives the user a central overview of
where and when he accessed certain podcast episodes, and allows clients to
synchronise states between applications. Refer to the :doc:`reference/events`
for further information.
