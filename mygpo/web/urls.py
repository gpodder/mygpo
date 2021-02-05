import re

from django.urls import path
from django.conf import settings
from django.views.generic.base import TemplateView, RedirectView
from django.views.static import serve

from mygpo.web.logo import CoverArt

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path(
        "logo/<int:size>/<str:prefix>/<str:filename>", CoverArt.as_view(), name="logo"
    ),
    # Media files are also served in production mode. For performance, these
    # files should be served by a reverse proxy in practice
    path(
        "%s<path:path>" % settings.MEDIA_URL.lstrip("/"),
        serve,
        name="media",
        kwargs=dict(document_root=settings.MEDIA_ROOT),
    ),
    path("tags/", views.mytags, name="tags"),
    path(
        "online-help",
        RedirectView.as_view(
            url="http://gpoddernet.readthedocs.org/en/latest/user/index.html",
            permanent=False,
        ),
        name="help",
    ),
    path("developer/", TemplateView.as_view(template_name="developer.html")),
    path(
        "contribute/",
        TemplateView.as_view(template_name="contribute.html"),
        name="contribute",
    ),
    path(
        "privacy/",
        TemplateView.as_view(template_name="privacy_policy.html"),
        name="privacy-policy",
    ),
]
