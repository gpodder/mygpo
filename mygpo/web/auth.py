from django.contrib.auth.backends import ModelBackend
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.sites.requests import RequestSite
from django.contrib.auth import get_user_model
from django.urls import reverse


class EmailAuthenticationBackend(ModelBackend):
    """Auth backend to enable login with email address as username"""

    def authenticate(self, request, username=None, password=None):
        try:
            validate_email(username)

            User = get_user_model()
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None

            return user if user.check_password(password) else None

        except ValidationError:
            return None
