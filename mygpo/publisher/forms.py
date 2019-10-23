from django import forms
from django.utils.translation import ugettext as _


class SearchPodcastForm(forms.Form):
    url = forms.URLField(label=_('URL'))
