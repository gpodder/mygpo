from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ImproperlyConfigured
from django.forms.fields import email_re
from django.db.models import get_model

class EmailAuthenticationBackend(ModelBackend):
    def authenticate(self, username=None, password=None):
        if email_re.search(username):
            try:
                user = User.objects.filter(email=username)[0]
                return user if user.check_password(password) else None
            except:
                return None
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

