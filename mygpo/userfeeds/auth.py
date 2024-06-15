from functools import wraps

from django.http import HttpResponse, HttpResponseBadRequest, Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model



#############################################################################
#
def view_or_basicauth(branch_coverage, view, request, username, token_name, realm="", *args, **kwargs):

    User = get_user_model()
    user = get_object_or_404(User, username=username)

    token = getattr(user, token_name, "")

    # check if a token is required at all
    if token == "":
        # Branch ID: 0
        branch_coverage[0] = True
        return view(request, username, *args, **kwargs)

    # this header format is used when passing auth-headers
    # from Aapache to fcgi
    if "AUTHORIZATION" in request.META:
        # Branch ID: 1
        branch_coverage[1] = True
        auth = request.META["AUTHORIZATION"]

    elif "HTTP_AUTHORIZATION" in request.META:
        # Branch ID: 2
        branch_coverage[2] = True
        auth = request.META["HTTP_AUTHORIZATION"]

    else:
        # Branch ID: 3
        branch_coverage[3] = True
        return auth_request()

    auth = auth.split(None, 1)

    if len(auth) == 2:
        # Branch ID: 4
        branch_coverage[4] = True
        auth_type, credentials = auth

        # NOTE: We are only support basic authentication for now.
        if auth_type.lower() == "basic":
            # Branch ID: 5
            branch_coverage[5] = True
            credentials = credentials.decode("base64").split(":", 1)
            if len(credentials) == 2:
                # Branch ID: 6
                branch_coverage[6] = True
                uname, passwd = credentials

                if uname != username:
                    # Branch ID: 7
                    branch_coverage[7] = True
                    return auth_request()

                if token == passwd:
                    # Branch ID: 8
                    branch_coverage[8] = True
                    return view(request, uname, *args, **kwargs)
            


    return auth_request()


def auth_request(realm=""):
    # Either they did not provide an authorization header or
    # something in the authorization attempt failed. Send a 401
    # back to them to ask them to authenticate.
    response = HttpResponse()
    response.status_code = 401
    response["WWW-Authenticate"] = 'Basic realm="%s"' % realm
    return response


#############################################################################
#
def require_token_auth(token_name):
    def wrapper(protected_view):
        @wraps(protected_view)
        def tmp(request, username, *args, **kwargs):
            return view_or_basicauth(
                protected_view, request, username, token_name, "", *args, **kwargs
            )

        return tmp

    return wrapper
