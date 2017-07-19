User Documentation
==================

`gpodder.net <https://gpodder.net>`_ is a web service to manage your podcast
subscriptions via the web. You can synchronize your devices, view status
information and discover new interesting podcasts online.

Supported Clients
-----------------

A list of supported clients is available in :ref:`clients`.

To configure gPodder to connect to gpodder.net, open the my.gpodder.org /
gpodder.net configuration dialog from the Subscriptions menu. Enter username
and password that you've used during the registration on the webservice. The
device ID is automatically generated from the hostname and will be used to
identify this specific device in the webservice. Next enable the
synchronisation of your subscription list. For the start, upload your
subscription list to the webservice. Subsequent changes will be transmitted
automatically.

Devices
-------

Each device connected to the webservice will be identified by its *Device ID*
which should therefore be unique (at least for your user account). *Do not try
to synchronize devices by using the same Device ID.*

A list of your devices can be found on the `devices page
<https://gpodder.net/devices/>`_.

Synchronizing Devices
^^^^^^^^^^^^^^^^^^^^^

If you have at least two devices connected to the webservice, you can
synchronize some of them. Open the device page for one of them, click
synchronize and select the device to synchronize with. After synchronizing, the
subscriptions of the devices will be merged. Adding a subscription at one
device will automatically add it to the others. Same for deletions.

The `device list <https://gpodder.net/devices/>`_ groups devices that are
synchronized with each other.

Episode States
--------------

Episode states (such as played, downloaded, etc) are synchronized across all devices.

Privacy Settings
----------------

By default we include information about your subscriptions in our `toplist
<https://gpodder.net/toplist/>`_ and `podcast suggestions
<https://gpodder.net/suggestions/>`_ . *We will never associate your username
and/or email address with your subscriptions on public pages.* You can even
opt-out from our anonymized statistics at the privacy page. If you mark some
podcasts as private, they will also not show up in your sharable subscription
list.

Sharing your Subscriptions
--------------------------

If you want to let others know about your which podcasts you are listening to,
go to your `sharing page <https://gpodder.net/share/>`_ . You can either share
your private URL with your friends or make it public and share your
subscriptions with the whole world.


.. toctree::
   :maxdepth: 2

   clients
