Podcast Lists API
=================

Podcast Lists are used to collect podcasts about one topic. On the website,
podcast lists are available at https://gpodder.net/lists/


Create Podcast List
-------------------

..  http:post:: /api/2/lists/(username)/create.(format)
    :synopsis: create a new podcast list

    * requires authenticaton
    * since 2.10

    :query title: url-encoded title
    :param username: username for which a new podcast list should be created
    :param format: see :ref:`formats`

    The list content is sent in the request body, in the format indicates by
    the format extension

    The server then generates a short name for the list from the title given in
    the Request. For example, from the title "My Python Podcasts" the name
    "my-python-podcasts" would be generated.

    :status 409: if the the user already has a podcast list with the
                 (generated) name
    :status 303: the podcast list has been created at the URL given in the
                 :http:header:`Location` header


Get User's Lists
----------------

..  http:get:: /api/2/lists/(username).json
    :synopsis: get a user's podcast lists

    * since 2.10

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK

        [
            {
                "title": "My Python Podcasts",
                "name": "my-python-podcasts",
                "web": "http://gpodder.net/user/a-user/lists/my-python-podcasts"
            }
        ]

    :status 200: the list of lists is returned
    :status 404: the user was not found


Get a Podcast List
------------------

..  http:get:: /api/2/lists/(username)/list/(listname).(format)
    :synopsis: get a podcast list

    * since 2.10

    :param username: username to which the list belongs
    :param listname: name of the requested podcast list
    :param format: see :ref:`formats`
    :status 200: the podcast list is returned in in the requested format
    :status 404: if the user or the list do not exist


Update a Podcast List
---------------------

..  http:put:: /api/2/lists/(username)/list/(listname).(format)
    :synopsis: update a podcast list

    * requires authentication
    * since 2.10

    :param username: username to which the list belongs
    :param listname: name of the requested podcast list
    :param format: see :ref:`formats`
    :status 404: if the user or the list do not exist
    :status 204: if the podcast list has been created / updated


Delete a Podcast List
---------------------

..  http:delete:: /api/2/lists/(username)/list/(listname).(format)
    :synopsis: delete a podcast list

    * requires authentication
    * since 2.10

    :param username: username to which the list belongs
    :param listname: name of the requested podcast list
    :param format: see :ref:`formats`
    :status 404: if the user or the list do not exist
    :status 204: if the podcast list has been deleted
