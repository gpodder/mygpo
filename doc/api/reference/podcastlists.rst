Podcast Lists API
=================

**TODO: this has just been copied from API 2 -- this needs review**

**Podcast Lists** are used to collect podcasts about some topics. On the
website, podcast lists are available at https://gpodder.net/lists/

Resources
---------

The Podcast Lists API defines the following resources ::

    /user/{username}/lists/create
    /user/{username}/lists
    /user/{username}/list/{listname}


Creating a Podcast List
-----------------------

A podcast list can be created by submitting a list of podcasts to the API.

Requires authentication.

Parameters
^^^^^^^^^^

* **title**: The title of the list (mandatory)


Request
^^^^^^^

Create a Podcast List ::

    POST /user/{username}/lists/create
    Content-Tpe: application/json

    {
        "title": "My Tech News",
        "podcasts": [
            { "url": "http://example.com/feed.xml" },
            ...
        ]
    }

The server then generates a short name for the list from the title given in the
request. For example, from the title "My Python Podcasts" the name
"my-python-podcasts" would be generated.

Responses
^^^^^^^^^

If the podcast list has been created successfully, ``303 See Other`` is
returned. ::

    303 See Other
    Location: /3/user/yourusername/list/yourlistname

The list can then be retrieved using a ``GET`` request.

If the list could not be created, an error code is returned. If another list
with the same (generated) name exists, ``409 Conflict`` is returned. ::

    {
        "message": "list already exists",
        "errors": [
            {
                field: "/title",
                code: "duplicate_list_name"
            }
        ]
    }


List the Podcast Lists of a User
--------------------------------


Request
^^^^^^^

List User's Lists ::

    GET /user/{username}/lists
    Content-Tpe: application/json


Response
^^^^^^^^

If the user exists, his/her podcast lists are returned. ::

    200 OK
    Content-Tpe: application/json

    {
        "podcastlists": [
            {
                "title": "My Python Podcasts",
                "name": "my-python-podcasts",
                "web": "http://gpodder.net/user/username/lists/my-python-podcasts"
            }
        ],
        "username": "username"
    }

If the user does not exist, ``404 Not Found`` is returned. ::

    404 Not Found
    Content-Tpe: application/json

    {
        "message": "user does not exist",
        "errors": [
            {
                field: "?username",
                code: "user_does_not_exist"
            }
        ]
    }


Retrieve Podcast List
---------------------

Request
^^^^^^^

Retrieve a Podcast List ::

    GET /user/{username}/list/{listname}
    Content-Tpe: application/json


Response
^^^^^^^^

The podcast list is returned. ::

    200 OK
    Content-Tpe: application/json

    {
        "title": "My Tech News",
        "name": "my-tech-news",
        "podcasts": [
            { "url": "http://example.com/feed.xml" },
            ...
        ],
        "username": "username",
    }


If either the user or the podcast list could not be found ``404 Not Found`` is
returned. ::

    404 Not Found
    Content-Tpe: application/json

    {
        "message": "podcast list does not exist",
        "errors": [
            {
                field: "?listname",
                code: "podcastlist_does_not_exist"
            }
        ]
    }


Update
------

Request
^^^^^^^

Update a Podcast List::

    PUT /user/{username}/list/{listname}
    Content-Tpe: application/json

    {
        "title": "My Tech News",
        "name": "my-tech-news2",
        "podcasts": [
            { "url": "http://example.org/feed-mp3.xml" },
            ...
        ]
    }

requires authentication


Response
^^^^^^^^

Possible Responses

* 404 Not Found if there is no list with the given name
* 204 No Content If the podcast list has been created / updated


Delete a Podcast List
---------------------

Request
^^^^^^^

Delete a Podcast List ::

    DELETE /user/{username}/list/{listname}

requires authentication


Response
^^^^^^^^

If the update was successful, ``204 No Content`` is returned. ::

    204 No Content

* 404 Not Found if there is no podcast list with the given name
