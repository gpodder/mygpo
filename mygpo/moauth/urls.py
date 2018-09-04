from django.conf.urls import url

from . import views


urlpatterns = [

    url(r'^oauth/login$',
        views.InitiateOAuthLogin.as_view(),
        name='login-oauth'),

    url(r'^oauth/callback$',
        views.OAuthCallback.as_view(),
        name='oauth-callback'),

]
