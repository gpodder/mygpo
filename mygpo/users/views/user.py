from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, get_user_model
from django.contrib import messages
from django.contrib.sites.requests import RequestSite
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

import requests
from oauth2client.client import FlowExchangeError

from mygpo.web.forms import RestorePasswordForm
from mygpo.constants import DEFAULT_LOGIN_REDIRECT
from mygpo.users.models import UserProxy
from mygpo.users.views.registration import send_activation_email
from mygpo.utils import random_token

import logging

logger = logging.getLogger(__name__)


def login(request, user):
    from django.contrib.auth import login

    login(request, user)


class LoginView(View):
    """View to login a user"""

    def get(self, request):
        """Shows the login page"""

        # Do not show login page for already-logged-in users
        if request.user.is_authenticated:
            return HttpResponseRedirect(DEFAULT_LOGIN_REDIRECT)

        return render(
            request,
            "login.html",
            {"url": RequestSite(request), "next": request.GET.get("next", "")},
        )

    @method_decorator(never_cache)
    def post(self, request):
        """Carries out the login, redirects to get if it fails"""

        # redirect target on successful login
        next_page = request.POST.get("next", "")

        # redirect target on failed login
        login_page = "{page}?next={next_page}".format(
            page=reverse("login"), next_page=next_page
        )

        username = request.POST.get("user", None)
        if not username:
            messages.error(request, _("Username missing"))
            return HttpResponseRedirect(login_page)

        password = request.POST.get("pwd", None)
        if not password:
            messages.error(request, _("Password missing"))
            return HttpResponseRedirect(login_page)

        # find the user from the configured login systems, and verify pwd
        user = authenticate(username=username, password=password)

        if not user:
            messages.error(request, _("Wrong username or password."))
            return HttpResponseRedirect(login_page)

        if not user.is_active:
            send_activation_email(user, request)
            messages.error(
                request,
                _(
                    "Please activate your account first. "
                    "We have just re-sent your activation email"
                ),
            )
            return HttpResponseRedirect(login_page)

        # set up the user's session
        login(request, user)

        if next_page:

            domain = RequestSite(request).domain
            allowed_hosts = [domain]
            if url_has_allowed_host_and_scheme(next_page, allowed_hosts):
                return HttpResponseRedirect(next_page)

            else:
                # TODO: log a warning that next_page is not
                # considered a safe redirect target
                pass

        return HttpResponseRedirect(DEFAULT_LOGIN_REDIRECT)


@never_cache
def restore_password(request):

    if request.method == "GET":
        form = RestorePasswordForm()
        return render(request, "restore_password.html", {"form": form})

    form = RestorePasswordForm(request.POST)
    if not form.is_valid():
        return HttpResponseRedirect("/login/")

    try:
        user = UserProxy.objects.all().by_username_or_email(
            form.cleaned_data["username"], form.cleaned_data["email"]
        )

    except UserProxy.DoesNotExist:
        messages.error(request, _("User does not exist."))
        return render(request, "password_reset_failed.html")

    if not user.is_active:
        send_activation_email(user, request)
        messages.error(
            request,
            _(
                "Please activate your account first. "
                "We have just re-sent your activation email"
            ),
        )
        return HttpResponseRedirect(reverse("login"))

    site = RequestSite(request)
    pwd = random_token(length=16)
    user.set_password(pwd)
    user.save()
    subject = render_to_string("reset-pwd-subj.txt", {"site": site}).strip()
    message = render_to_string(
        "reset-pwd-msg.txt", {"username": user.username, "site": site, "password": pwd}
    )
    user.email_user(subject, message)
    return render(request, "password_reset.html")
