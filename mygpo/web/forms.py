from django import forms
from django.utils.translation import ugettext as _

class UserAccountForm(forms.Form):
    email = forms.EmailField(label=_('Your Email Address'))
    public = forms.BooleanField(required=False, label=_('May we use your subscriptions for the toplist and suggestions?'))

