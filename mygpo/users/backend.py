from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

import logging
logger = logging.getLogger(__name__)


class CaseInsensitiveModelBackend(ModelBackend):
    """ Authenticates with a case-insensitive username """

    def authenticate(self, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        users = UserModel.objects.filter(username__iexact=username)\
                                 .order_by('-last_login')
        if users.count() == 0:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)
            return None

        if users.count() > 1:
            logger.error('Login with non-unique username: %s', username)

        user = users[0]
        if user.check_password(password):
            return user
