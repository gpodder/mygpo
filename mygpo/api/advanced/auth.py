from datetime import datetime, timedelta

from django.contrib import auth
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache

from mygpo.api.basic_auth import require_valid_user, check_username
from mygpo.decorators import allowed_methods, cors_origin


@csrf_exempt
@require_valid_user
@check_username
@allowed_methods(['POST'])
@never_cache
@cors_origin()
def login(request, username):
    """
    authenticates the user with regular http basic auth
    """

    request.session.set_expiry(datetime.utcnow() + timedelta(days=365))
    return HttpResponse()


@csrf_exempt
@check_username
@allowed_methods(['POST'])
@never_cache
@cors_origin()
def logout(request, username):
    """
    logs out the user. does nothing if he wasn't logged in
    """

    auth.logout(request)
    return HttpResponse()
