from functools import wraps

from django.http import HttpResponseRedirect

from mygpo.publisher.models import PublishedPodcast


def require_publisher(protected_view):
    @wraps(protected_view)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return HttpResponseRedirect('/login/')

        if is_publisher(request.user):
            return protected_view(request, *args, **kwargs)

        return HttpResponseRedirect('/')

    return wrapper


def is_publisher(user):
    """
    checks if the given user has publisher rights,
    ie he is either set as the publisher of at least one podcast,
    or he has the staff flag set
    """

    if not user.is_authenticated:
        return False

    if user.is_staff:
        return True

    if PublishedPodcast.objects.filter(publisher=user).exists():
        return True

    return False
