Device Synchronization API
==========================

Get Sync Status
---------------

..  http:get:: /api/2/sync-devices/(username).json
    :synopsis: get the sync status of a user

    * requires authentication
    * since 2.10

    **Example response**:

    .. sourcecode:: http

        {
          "synchronized": [
               ["notebook", "n900"],
               ["pc-home", "pc-work"],
            ],
          "not-synchronized": [
               "test-pc", "netbook"
            ]
        }

    :param username: username for which the sync status is requested


Start / Stop Sync
-----------------

..  http:post:: /api/2/sync-devices/(username).json
    :synopsis: update the sync status of a user's devices

    * requires authentication
    * since 2.10

    **Example request**:

    .. sourcecode:: http

        {
          "synchronize": [
               ["notebook", "netbook"]
             ],
          "stop-synchronize": ["pc-work"]
        }

    Sets up / stops synchronization between devices. The synchronization status
    is sent as a response

    **Example status**:

    .. sourcecode:: http

        {
          "synchronized": [
               ["notebook", "netbook", "n900"]
           ],
          "not-synchronized": [
               "test-pc", "pc-work", "pc-home"
           ]
        }

    :param username: username for which the sync status is requested
