from django.conf.urls import url
from django.views.generic.base import TemplateView, RedirectView

from mygpo.web.logo import CoverArt

from . import views


urlpatterns = [

    url(r'^$',
        views.home,
        name='home'),

    url(r'^logo/(?P<size>\d+)/(?P<filename>[^/]*)$',
        CoverArt.as_view(),
        name='logo'),

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
