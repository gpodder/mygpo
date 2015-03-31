from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from mygpo.api import APIView
from mygpo.decorators import requires_token
from mygpo.subscriptions import get_subscribed_podcasts


class UserSubscriptions(APIView):
    @requires_token(token_name='subscriptions_token')
    def get(self, request, username):
        User = get_user_model()
        user = get_object_or_404(User, username=username)
        subscriptions = get_subscribed_podcasts(user, only_public=True)
        token = user.profile.get_token('subscriptions_token')

        return {
            'subscriptions': subscriptions,
            'other_user': user,
            'token': token,
        }
