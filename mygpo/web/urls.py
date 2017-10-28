import re

from django.conf.urls import url
from django.conf import settings
from django.views.generic.base import TemplateView, RedirectView
from django.views.static import serve

from mygpo.web.logo import CoverArt

from . import views


urlpatterns = [

    url(r'^$',
        views.home,
        name='home'),

    url(r'^logo/(?P<size>\d+)/(?P<filename>[^/]*)$',
        CoverArt.as_view(),
        name='logo'),

    # Media files are also served in production mode. For performance, these
    # files should be served by a reverse proxy in practice
    url(r'^%s(?P<path>.*)$' % re.escape(settings.MEDIA_URL.lstrip('/')),
        serve,
        name='media',
        kwargs=dict(document_root=settings.MEDIA_ROOT)
    ),

    url(r'^tags/',
        views.mytags,
        name='tags'),

    url(r'^online-help',
        RedirectView.as_view(
            url='http://gpoddernet.readthedocs.org/en/latest/user/index.html',
            permanent=False,
        ),
        name='help'),

    url(r'^developer/',
        TemplateView.as_view(template_name='developer.html')),

    url(r'^contribute/',
        TemplateView.as_view(template_name='contribute.html'),
        name='contribute'),

    url(r'^privacy/',
        TemplateView.as_view(template_name='privacy_policy.html'),
        name='privacy-policy'),

]
