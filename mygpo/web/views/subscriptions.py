from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model

from mygpo.utils import parse_bool
from mygpo.decorators import requires_token
from mygpo.subscriptions import get_subscribed_podcasts
from mygpo.web.utils import symbian_opml_changes


@requires_token(token_name='subscriptions_token', denied_template='user_subscriptions_denied.html')
def for_user(request, username):
    User = get_user_model()
    user = get_object_or_404(User, username=username)
    subscriptions = get_subscribed_podcasts(user, only_public=True)
    token = user.profile.get_token('subscriptions_token')

    return render(request, 'user_subscriptions.html', {
        'subscriptions': subscriptions,
        'other_user': user,
        'token': token,
        })

@requires_token(token_name='subscriptions_token')
def for_user_opml(request, username):
    User = get_user_model()
    user = get_object_or_404(User, username=username)
    subscriptions = get_subscribed_podcasts(user, only_public=True)

    if parse_bool(request.GET.get('symbian', False)):
        subscriptions = list(map(symbian_opml_changes, subscriptions))

    response = render(request, 'user_subscriptions.opml', {
        'subscriptions': subscriptions,
        'other_user': user
        })
    response['Content-Disposition'] = 'attachment; filename=%s-subscriptions.opml' % username
    return response
