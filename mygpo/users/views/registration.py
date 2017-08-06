import re

from django.http import HttpResponseRedirect
from django.views import View
from django.conf import settings


class RegistrationView(View):
    """ View to register a new user """

    def get(self, request):
        url = settings.MYGPO_AUTH_REGISTER_URL
        return HttpResponseRedirect(url)
