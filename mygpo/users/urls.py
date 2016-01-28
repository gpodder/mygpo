from django.conf.urls import url
from django.views.generic.base import TemplateView

from .views import registration

urlpatterns = [

 url(r'^register/$',
     registration.RegistrationView.as_view(),
     name='register'),

 url(r'^registration_complete/$',
    registration.TemplateView.as_view(template_name='registration/registration_complete.html'),
    name='registration-complete'),

 url(r'^activate/(?P<activation_key>\w+)$',
     registration.ActivationView.as_view()),

 url(r'^registration/resend$',
    registration.ResendActivationView.as_view(),
    name='resend-activation'),

 url(r'^registration/resent$',
    registration.ResentActivationView.as_view(),
    name='resent-activation'),
]
