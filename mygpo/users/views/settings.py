from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django.contrib import messages
from django.forms import ValidationError
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.requests import RequestSite
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache, cache_control
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from django.utils.html import strip_tags

from mygpo.podcasts.models import Podcast
from mygpo.usersettings.models import UserSettings
from mygpo.decorators import allowed_methods
from mygpo.web.forms import UserAccountForm, ProfileForm
from mygpo.web.utils import normalize_twitter
from mygpo.users.settings import PUBLIC_SUB_USER, PUBLIC_SUB_PODCAST


@login_required
@vary_on_cookie
@cache_control(private=True)
@allowed_methods(["GET", "POST"])
def account(request):

    if request.method == "GET":

        site = RequestSite(request)
        userpage_token = request.user.profile.get_token("userpage_token")

        profile_form = ProfileForm(
            {
                "twitter": request.user.profile.twitter,
                "about": request.user.profile.about,
            }
        )

        form = UserAccountForm(
            {
                "email": request.user.email,
                "public": request.user.profile.settings.get_wksetting(PUBLIC_SUB_USER),
            }
        )

        return render(
            request,
            "account.html",
            {
                "site": site,
                "form": form,
                "profile_form": profile_form,
                "userpage_token": userpage_token,
            },
        )

    try:
        form = UserAccountForm(request.POST)

        if not form.is_valid():
            raise ValueError(
                _(
                    "Oops! Something went wrong. Please double-check the data you entered."
                )
            )

        if form.cleaned_data["password_current"]:
            if not request.user.check_password(form.cleaned_data["password_current"]):
                raise ValueError("Current password is incorrect")

            request.user.set_password(form.cleaned_data["password1"])

        request.user.email = form.cleaned_data["email"]

        try:
            request.user.save()
        except Exception as ex:
            # TODO: which exception?
            messages.error(request, str(ex))

        messages.success(request, "Account updated")

    except (ValueError, ValidationError) as e:
        messages.error(request, str(e))

    return render(request, "account.html", {"form": form})


class ProfileView(View):
    """Updates the public profile and redirects back to the account view"""

    def post(self, request):
        user = request.user

        form = ProfileForm(request.POST)

        if not form.is_valid():
            raise ValueError(
                _(
                    "Oops! Something went wrong. Please double-check the data you entered."
                )
            )

        request.user.twitter = normalize_twitter(form.cleaned_data["twitter"])
        request.user.about = strip_tags(form.cleaned_data["about"])

        request.user.save()
        messages.success(request, _("Data updated"))

        return HttpResponseRedirect(reverse("account") + "#profile")


class AccountRemoveGoogle(View):
    """Removes the connected Google account"""

    @method_decorator(login_required)
    def post(self, request):
        request.user.google_email = None
        request.user.save()
        messages.success(request, _("Your account has been disconnected"))
        return HttpResponseRedirect(reverse("account"))


@login_required
@never_cache
@allowed_methods(["GET", "POST"])
def delete_account(request):

    if request.method == "GET":
        return render(request, "delete_account.html")

    user = request.user
    user.is_active = False
    user.save()
    logout(request)
    return render(request, "deleted_account.html")


class DefaultPrivacySettings(View):

    public = True

    @method_decorator(login_required)
    @method_decorator(never_cache)
    def post(self, request):
        settings = request.user.profile.settings
        settings.set_setting(PUBLIC_SUB_USER.name, self.public)
        settings.save()
        return HttpResponseRedirect(reverse("privacy"))


class PodcastPrivacySettings(View):

    public = True

    @method_decorator(login_required)
    @method_decorator(never_cache)
    def post(self, request, podcast_id):
        podcast = Podcast.objects.get(id=podcast_id)

        settings, created = UserSettings.objects.get_or_create(
            user=request.user,
            content_type=ContentType.objects.get_for_model(podcast),
            object_id=podcast.pk,
        )

        settings.set_wksetting(PUBLIC_SUB_PODCAST, self.public)
        settings.save()
        return HttpResponseRedirect(reverse("privacy"))


@login_required
@never_cache
def privacy(request):
    site = RequestSite(request)
    user = request.user

    podcasts = (
        Podcast.objects.filter(subscription__user=user)
        .distinct("pk")
        .prefetch_related("slugs")
    )
    private = UserSettings.objects.get_private_podcasts(user)

    subscriptions = []
    for podcast in podcasts:

        subscriptions.append((podcast, podcast in private))

    return render(
        request,
        "privacy.html",
        {
            "private_subscriptions": not request.user.profile.settings.get_wksetting(
                PUBLIC_SUB_USER
            ),
            "subscriptions": subscriptions,
            "domain": site.domain,
        },
    )


@vary_on_cookie
@cache_control(private=True)
@login_required
def share(request):
    site = RequestSite(request)

    user = request.user

    if "public_subscriptions" in request.GET:
        user.profile.subscriptions_token = ""
        user.profile.save()

    elif "private_subscriptions" in request.GET:
        user.profile.create_new_token("subscriptions_token")
        user.profile.save()

    token = user.profile.get_token("subscriptions_token")

    return render(request, "share.html", {"site": site, "token": token})
