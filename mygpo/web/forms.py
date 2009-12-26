from django import forms
from django.utils.translation import ugettext as _
from mygpo.api.models import Device, DEVICE_TYPES

class UserAccountForm(forms.Form):
    email = forms.EmailField(label=_('Your Email Address'))
    public = forms.BooleanField(required=False, label=_('May we use your subscriptions for the toplist and suggestions?'))

class DeviceForm(forms.Form):
    name = forms.CharField(max_length=100, label=_('Name of this device'))
    type = forms.ChoiceField(choices=DEVICE_TYPES, label=_('What kind of device is this?'))
    uid = forms.CharField(max_length=50, label=_('What UID is configured on the pysical device?'))


class SyncForm(forms.Form):
    targets = forms.CharField()

#    def __init__(self, device=None, *args, **kwargs):
#        super( SyncForm, self ).__init__(*args, **kwargs)
#
#        targets = self.sync_target_choices(device.sync_targets())
#        self.fields['targets'] = forms.ChoiceField(choices=targets, label=_('Synchronize with the following devices'))
#
    def set_device(self, device):
        targets = self.sync_target_choices(device.sync_targets())
        self.fields['targets'] = forms.ChoiceField(choices=targets, label=_('Synchronize with the following devices'))

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

