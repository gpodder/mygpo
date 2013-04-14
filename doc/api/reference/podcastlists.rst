Podcast Lists API
=================

**TODO: this has just been copied from API 2 -- this needs review**

**Podcast Lists** are used to collect podcasts about some topics. On the
website, podcast lists are available at https://gpodder.net/lists/

Resources
---------

The Podcast Lists API defines the following resources ::

    none yet


Creating a Podcast List
-----------------------

Create a Podcast List ::

    POST /api/2/lists/<username>/create.<format>?title=<url-encoded title>
    The list content is sent in the request body, in the format indicates by the format extension

    requires authenticaton

The server then generates a short name for the list from the title given in the
Request. For example, from the title "My Python Podcasts" the name
"my-python-podcasts" would be generated.

Possible Responses

* 409 Conflict: if the the user already has a podcast list with the (generated) name
* 303 See Other: the podcast list has been created at the URL given in the Location header


List the Podcast Lists of a User
--------------------------------
List User's Lists ::

    GET /api/2/lists/<username>.json


Possible Responses

* 200 OK, the list of lists in the format given below

Response ::

    [
        {"title": "My Python Podcasts", "name": "my-python-podcasts", "web": "http://gpodder.net/user/<username>/lists/my-python-podcasts" }
    ]


Retrieve Podcast List
---------------------

Retrieve a Podcast List ::

    GET /api/2/lists/<username>/list/<list-name>.<format>


Possible Responses

* 404 Not Found if there is no list with the given name
* 200 OK and the podcast list in the given format


Update
------

Update a Podcast List::

    PUT /api/2/lists/<username>/list/<list-name>.<format>

requires authentication


Possible Responses

* 404 Not Found if there is no list with the given name
* 204 No Content If the podcast list has been created / updated


Delete a Podcast List
---------------------

Delete a Podcast List ::

    DELETE /api/2/lists/<username>/list/<list-name>.<format>

requires authentication

Possible Responses

* 404 Not Found if there is no podcast list with the given name
* 204 No Content if the list has been deleted.
