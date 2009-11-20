#http://scottbarnham.com/blog/2008/08/21/extending-the-django-user-model-with-inheritance/

from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ImproperlyConfigured
from django.forms.fields import email_re
from django.db.models import get_model

class UserAccountModelBackend(ModelBackend):
    def authenticate(self, username=None, password=None):
        if email_re.search(username):
            try:
                user = self.user_class.objects.get(email=username)
            except self.user_class.DoesNotExist:
                return None
        else:
            try:
                user = self.user_class.objects.get(username=username)
            except self.user_class.DoesNotExist:
                return None
        if user.check_password(password):
                    return user

    def get_user(self, user_id):
        try:
            return self.user_class.objects.get(pk=user_id)
        except self.user_class.DoesNotExist:
            return None

    @property
    def user_class(self):
        if not hasattr(self, '_user_class'):
            self._user_class = get_model(*settings.CUSTOM_USER_MODEL.split('.', 2))
            if not self._user_class:
                raise ImproperlyConfigured('Could not get custom user model')
        return self._user_class

