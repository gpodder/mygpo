from django import forms
from django.utils.translation import ugettext as _
from mygpo.api.models import DEVICE_TYPES

class UserAccountForm(forms.Form):
    email = forms.EmailField(label=_('Your Email Address'))
    public = forms.BooleanField(required=False, label=_('May we use your subscriptions for the toplist and suggestions?'))

class DeviceForm(forms.Form):
    name = forms.CharField(max_length=100, label=_('Name of this device'))
    type = forms.ChoiceField(choices=DEVICE_TYPES, label=_('What kind of device is this?'))
    uid = forms.CharField(max_length=50, label=_('What UID is configured on the pysical device?'))

