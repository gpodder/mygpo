from django import forms
from django.utils.translation import gettext as _


class SearchPodcastForm(forms.Form):
    url = forms.URLField(label=_("URL"))
