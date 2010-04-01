from django import forms
from django.utils.translation import ugettext as _
from django.forms.util import ValidationError
from mygpo.api.models import Device, DEVICE_TYPES, SyncGroup
from mygpo.log import log
import re

class UserAccountForm(forms.Form):
    """
    the form that is used in the account settings.

    if one of the three password fields is set, a password change is assumed
    and the current and new passwords are checked.
    """
    email = forms.EmailField(label=_('E-Mail address'))
    public = forms.BooleanField(required=False, label=_('Use subscriptions in toplist and suggestions'))
    password_current = forms.CharField(label=_(u'Current password'),widget=forms.PasswordInput(render_value=False), required=False)
    password1 = forms.CharField(label=_(u'New password'),widget=forms.PasswordInput(render_value=False), required=False)
    password2 = forms.CharField(label=_(u'Confirm password'),widget=forms.PasswordInput(render_value=False), required=False)

    def is_valid(self):
        if not super(UserAccountForm, self).is_valid(): return False

        if self.cleaned_data['password_current'] or self.cleaned_data['password1'] or self.cleaned_data['password2']:
            if self.cleaned_data['password_current'] == '':
                return False #must give current password

            if self.cleaned_data['password1'] == '':
                return False #cant set empty password

            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                return False #must confirm password

        return True

class DeviceForm(forms.Form):
    """
    form for editing device information by a user.
    """
    name = forms.CharField(max_length=100, label=_('Name of this device'))
    type = forms.ChoiceField(choices=DEVICE_TYPES, label=_('What kind of device is this?'))
    uid = forms.CharField(max_length=50, label=_('What UID is configured on the physical device?'))

class PrivacyForm(forms.Form):
    """
    Form for editing the privacy settings for a subscription. It is shown on a
    podcast page if the current user is subscribed to the podcast.
    """
    public = forms.BooleanField(required=False, label=_('Include this subscription in shared subscription list and anonymous statistics'))

class SyncForm(forms.Form):
    """
    Form that is used to select either a single devices or a device group.
    """

    targets = forms.CharField()

    def set_targets(self, sync_targets, label=''):
        targets = self.sync_target_choices(sync_targets)
        self.fields['targets'] = forms.ChoiceField(choices=targets, label=label)

    def sync_target_choices(self, targets):
        """
        returns a list of tuples that can be used as choices for a ChoiceField.
        the first item in each tuple is a letter identifying the type of the 
        sync-target - either d for a Device, or g for a SyncGroup. This letter
        is followed by the id of the target.
        The second item in each tuple is the string-representation of the #
        target.
        """
        return [('%s%s' % ('d' if isinstance(t, Device) else 'g', t.id), t) for t in targets]


    def get_target(self):
        """
        returns the target (device or device group) that has been selected
        in the form.
        """
        if not self.is_valid():
            log('no target given in SyncForm')
            raise ValueError(_('No device selected'))

        target = self.cleaned_data['targets']
        m = re.match('^([dg])(\d+)$', target)
        if m == None:
            log('invalid target %s given in SyncForm' % target)
            raise ValueError(_('Invalid device selected: %s') % target)

        if m.group(1) == 'd':
            return Device.objects.get(pk=m.group(2))
        else:
            return SyncGroup.objects.get(pk=m.group(2))

class ResendActivationForm(forms.Form):
    username = forms.CharField(max_length=100, label=_('Please enter your username'), required=False)
    email = forms.CharField(max_length=100, label=_('or the email address used while registering'), required=False)


class RestorePasswordForm(forms.Form):
    username = forms.CharField(max_length=100, label=_('Please enter your username'), required=False)
    email = forms.CharField(max_length=100, label=_('or the email address used while registering'), required=False)
