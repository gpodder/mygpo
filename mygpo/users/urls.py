from django.conf.urls import url
from django.views.generic.base import TemplateView

from mygpo.users.views.registration import (RegistrationView, ActivationView,
    ResendActivationView, ResentActivationView,)

urlpatterns = [

 url(r'^register/$',
     RegistrationView.as_view(),
     name='register'),

 url(r'^registration_complete/$',
    TemplateView.as_view(template_name='registration/registration_complete.html'),
    name='registration-complete'),

 url(r'^activate/(?P<activation_key>\w+)$',
     ActivationView.as_view()),

 url(r'^registration/resend$',
    ResendActivationView.as_view(),
    name='resend-activation'),

 url(r'^registration/resent$',
    ResentActivationView.as_view(),
    name='resent-activation'),
]
