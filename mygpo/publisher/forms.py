from django import forms
from django.utils.translation import ugettext as _
from mygpo.api.models import Podcast, Episode

class SearchPodcastForm(forms.Form):
    url = forms.URLField(label=_('URL'))


class EpisodeForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(EpisodeForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            self.fields['url'].widget.attrs['readonly'] = True

    def clean_url(self):
        return self.instance.url

    class Meta:
        model = Episode
        fields = ('title', 'url', 'description', 'link', 'timestamp', 'author', 'duration')


class PodcastForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(PodcastForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            self.fields['url'].widget.attrs['readonly'] = True

    def clean_url(self):
        return self.instance.url

    class Meta:
        model = Podcast
        fields = ('title', 'url', 'description', 'link', 'logo_url', 'author', 'language')

