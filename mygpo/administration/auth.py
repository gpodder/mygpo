from functools import wraps

from django.http import Http404, HttpResponseRedirect
from django.conf import settings


def require_staff(protected_view):
    @wraps(protected_view)
    def wrapper(request, *args, **kwargs):

        staff_token = settings.STAFF_TOKEN
        token_auth = staff_token is not None and staff_token == request.GET.get(
            'staff', None
        )
        if token_auth:
            return protected_view(request, *args, **kwargs)

        if not request.user.is_authenticated:
            return HttpResponseRedirect('/login/')

        if request.user.is_staff:
            return protected_view(request, *args, **kwargs)

        raise Http404

    return wrapper
