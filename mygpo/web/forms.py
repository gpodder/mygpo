import re

from django import forms
from django.utils.translation import ugettext as _

from mygpo.users.models import Client

import logging
logger = logging.getLogger(__name__)


class UserAccountForm(forms.Form):
    """
    the form that is used in the account settings.

    if one of the three password fields is set, a password change is assumed
    and the current and new passwords are checked.
    """
    email = forms.EmailField(
        label=_('E-Mail address'),
        widget=forms.TextInput(attrs={
            'class': 'input input-sm form-control',
        }),
        required=True)

    password_current = forms.CharField(
        label=_(u'Current password'),
        widget=forms.PasswordInput(render_value=False, attrs={
            'class': 'input input-sm form-control',
        }),
        required=False)

    password1 = forms.CharField(
        label=_(u'New password'),
        widget=forms.PasswordInput(render_value=False, attrs={
            'class': 'input input-sm form-control',
        }),
        required=False)

    password2 = forms.CharField(
        label=_(u'Confirm password'),
        widget=forms.PasswordInput(render_value=False, attrs={
            'class': 'input input-sm form-control',
        }),
        required=False)

    def is_valid(self):
        if not super(UserAccountForm, self).is_valid():
            return False

        pw1 = self.cleaned_data['password1']
        pw2 = self.cleaned_data['password2']

        if self.cleaned_data['password_current'] or pw1 or pw2:

            if self.cleaned_data['password_current'] == '':
                return False  # must give current password

            if pw1 == '':
                return False  # cant set empty password

            if pw1 != pw2:
                return False  # 5must confirm password

        return True


class ProfileForm(forms.Form):
    twitter = forms.CharField(
        label=_(u'Twitter'),
        widget=forms.TextInput(attrs={
            'class': 'input input-sm form-control',
        }),
        required=False,
    )

    about = forms.CharField(
        label=_(u'A few words about you'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'input input-sm form-control',
        }),
        help_text='You can use Markdown',
    )


class FlattrForm(forms.Form):
    """ Per-user Flattr settings """

    # Authentication token; empty or None when not signed in
    token = forms.CharField(
        required=False,
        label=_('Token'))

    # Auto-flattring enabled
    enable = forms.BooleanField(
        required=False,
        label=_('Auto-Flattr played episodes'),
        widget=forms.CheckboxInput(attrs={
            'class': 'input input-sm form-control',
        }),
    )

    # Auto-flattr mygpo (or whatever the FLATTR_MYGPO_THING
    # in settings_prod.py is) on every other flattr
    flattr_mygpo = forms.BooleanField(
        required=False,
        label=_('Flattr us'),
        widget=forms.CheckboxInput(attrs={
            'class': 'input input-sm form-control',
        }),
    )

    # username under which own content (eg podcast lists) should be published
    username = forms.CharField(
        required=False,
        label=_('Username for own content'),
        widget=forms.TextInput(attrs={
            'class': 'input input-sm form-control',
            'placeholder': 'Device Name',
        }),
    )


class DeviceForm(forms.Form):
    """
    form for editing device information by a user.
    """
    name = forms.CharField(max_length=100, label=_('Name'),
                widget=forms.TextInput(attrs={
                    'class': 'input input-sm form-control',
                    'placeholder': 'Device Name',
                }))
    type = forms.ChoiceField(choices=Client.TYPES, label=_('Type'),
                widget=forms.Select(attrs={
                    'class': 'input input-sm form-control',
                }))
    uid = forms.CharField(max_length=50, label=_('Device ID'),
                widget=forms.TextInput(attrs={
                    'class': 'input input-sm form-control',
                    'placeholder': _('ID on device'),
                }))


class PrivacyForm(forms.Form):
    """
    Form for editing the privacy settings for a subscription. It is shown on a
    podcast page if the current user is subscribed to the podcast.
    """

    public = forms.BooleanField(
        required=False,
        label=_('Share this subscription with other users (public)'))


class SyncForm(forms.Form):
    """
    Form that is used to select either a single devices or a device group.
    """

    targets = forms.CharField(
            widget = forms.Select(attrs={
                'class': 'input input-sm form-control',
            }),
        )

    def set_targets(self, sync_targets, label=''):
        targets = map(self.sync_target_choice, sync_targets)
        self.fields['targets'] = forms.ChoiceField(
            choices=targets,
            label=label)

    def sync_target_choice(self, target):
        """
        returns a list of tuples that can be used as choices for a ChoiceField.
        the first item in each tuple is a letter identifying the type of the
        sync-target - either d for a Device, or g for a SyncGroup. This letter
        is followed by the id of the target.
        The second item in each tuple is the string-representation of the #
        target.
        """

        if isinstance(target, Client):
            return (target.uid, target.name)

        elif isinstance(target, list):
            return (target[0].uid, ', '.join(d.name for d in target))

    def get_target(self):
        """
        returns the target (device or device group) that has been selected
        in the form.
        """
        if not self.is_valid():
            logger.warn('no target given in SyncForm')
            raise ValueError(_('No device selected'))

        target = self.cleaned_data['targets']
        return target


class ResendActivationForm(forms.Form):
    username = forms.CharField(
        max_length=100,
        label=_('Please enter your username'),
        required=False)

    email = forms.CharField(
        max_length=100,
        label=_('or the email address used while registering'),
        required=False)


class RestorePasswordForm(forms.Form):
    username = forms.CharField(
        max_length=100,
        label=_('Username'),
        required=False)

    email = forms.CharField(
        max_length=100,
        label=_('E-Mail address'),
        required=False)
