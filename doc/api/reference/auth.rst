Authentication API
==================

Login / Verify Login
--------------------

..  http:post:: /api/2/auth/(username)/login.json
    :synopsis: verify the login status

    * since 2.10

    Log in the given user for the given device via HTTP Basic Auth.

    :param username: the username which should be logged in
    :status 401: If the URL is accessed without login credentials provided
    :status 400: If the client provides a cookie, but for a different username than the one given
    :status 200: the response headers have a ``sessionid`` cookie set.

    The client can use this URL with the cookie in the request header to check
    if the cookie is still valid.


Logout
------

..  http:post:: /api/2/auth/(username)/logout.json
    :synopsis: logout

    * since 2.10

    Log out the given user. Removes the session ID from the database.

    :param username: the username which should be logged out
    :status 200: if the client didn't send a cookie, or the user was
                 successfully logged out
    :status 400: if the client provides a cookie, but for a different username than the one given
