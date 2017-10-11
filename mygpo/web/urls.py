from django.urls import path
from django.views.generic.base import TemplateView, RedirectView

from mygpo.web.logo import CoverArt

from . import views


urlpatterns = [

    path('',
        views.home,
        name='home'),

    path('logo/<int:size>/<str:prefix>/<str:filename>$',
        CoverArt.as_view(),
        name='logo'),

    path('tags/',
        views.mytags,
        name='tags'),

    path('online-help',
        RedirectView.as_view(
            url='http://gpoddernet.readthedocs.org/en/latest/user/index.html',
            permanent=False,
        ),
        name='help'),

    path('developer/',
        TemplateView.as_view(template_name='developer.html')),

    path('contribute/',
        TemplateView.as_view(template_name='contribute.html'),
        name='contribute'),

    path('privacy/',
        TemplateView.as_view(template_name='privacy_policy.html'),
        name='privacy-policy'),

]
