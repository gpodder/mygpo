import re

from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.views.generic.edit import FormView
from django.utils.translation import ugettext as _
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.base import View
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site

from mygpo.utils import random_token
from mygpo.users.models import UserProxy


USERNAME_MAXLEN = get_user_model()._meta.get_field('username').max_length

USERNAME_REGEX = re.compile(r'^\w[\w.+-]*$')


class UsernameValidator(RegexValidator):
    """ Validates that a username uses only allowed characters """
    regex = USERNAME_REGEX
    message = 'Invalid Username'
    code='invalid-username'


class RegistrationForm(forms.Form):
    """ Form that is used to register a new user """
    username = forms.CharField(max_length=USERNAME_MAXLEN,
                               validators=[UsernameValidator()],
                              )
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if not password1 or password1 != password2:
            raise forms.ValidationError('Passwords do not match')


class RegistrationView(FormView):
    """ View to register a new user """
    template_name = 'registration/registration_form.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('registration-complete')

    def form_valid(self, form):
        """ called whene the form was POSTed and its contents were valid """

        try:
            user = self.create_user(form)

        except ValidationError as e:
            messages.error(self.request, '; '.join(e.messages))
            return HttpResponseRedirect(reverse('register'))

        except IntegrityError:
            messages.error(self.request,
                           _('Username or email address already in use'))
            return HttpResponseRedirect(reverse('register'))

        send_activation_email(user, self.request)
        return super(RegistrationView, self).form_valid(form)

    @transaction.atomic
    def create_user(self, form):
        User = get_user_model()
        user = User()
        user.username = form.cleaned_data['username']

        email_addr = form.cleaned_data['email']
        user.email = email_addr

        user.set_password(form.cleaned_data['password1'])
        user.is_active = False
        user.full_clean()

        try:
            user.save()

        except IntegrityError as e:
            if 'django_auth_unique_email' in str(e):
                # this was not caught by the form validation, but now validates
                # the DB's unique constraint
                raise ValidationError('The email address {0} is '
                                      'already in use.'.format(email_addr))
            else:
                raise

        user.profile.activation_key = random_token()
        user.profile.save()

        return user


class ActivationView(TemplateView):
    """ Activates an already registered user """

    template_name = 'registration/activation_failed.html'

    def get(self, request, activation_key):
        User = get_user_model()

        try:
            user = UserProxy.objects.get(
                profile__activation_key=activation_key,
                is_active=False,
            )
        except UserProxy.DoesNotExist:
            messages.error(request, _('The activation link is either not '
                                      'valid or has already expired.'))
            return super(ActivationView, self).get(request, activation_key)

        user.activate()
        messages.success(request, _('Your user has been activated. '
                                    'You can log in now.'))
        return HttpResponseRedirect(reverse('login'))


class ResendActivationForm(forms.Form):
    """ Form for resending the activation email """

    username = forms.CharField(max_length=USERNAME_MAXLEN, required=False)
    email = forms.EmailField(required=False)

    def clean(self):
        cleaned_data = super(ResendActivationForm, self).clean()
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')

        if not username and not email:
            raise forms.ValidationError(_('Either username or email address '
                                          'are required.'))


class ResendActivationView(FormView):
    """ View to resend the activation email """
    template_name = 'registration/resend_activation.html'
    form_class = ResendActivationForm
    success_url = reverse_lazy('resent-activation')

    def form_valid(self, form):
        """ called whene the form was POSTed and its contents were valid """

        try:
            user = UserProxy.objects.all().by_username_or_email(
                form.cleaned_data['username'],
                form.cleaned_data['email'],
            )

        except UserProxy.DoesNotExist:
            messages.error(self.request, _('User does not exist.'))
            return HttpResponseRedirect(reverse('resend-activation'))

        if user.profile.activation_key is None:
            messages.success(self.request, _('Your account already has been '
                                             'activated. Go ahead and log in.'))

        send_activation_email(user, self.request)
        return super(ResendActivationView, self).form_valid(form)


class ResentActivationView(TemplateView):
    template_name = 'registration/resent_activation.html'


def send_activation_email(user, request):
    """ Sends the activation email for the given user """

    subj = render_to_string('registration/activation_email_subject.txt')
    # remove trailing newline added by render_to_string
    subj = subj.strip()

    msg = render_to_string('registration/activation_email.txt', {
        'site': get_current_site(request),
        'activation_key': user.profile.activation_key,
    })
    user.email_user(subj, msg)
