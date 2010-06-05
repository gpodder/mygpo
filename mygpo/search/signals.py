from django.db.models.signals import post_save, pre_delete
from mygpo.api.models import Podcast, PodcastGroup
from mygpo.search.models import SearchEntry
from mygpo.search.util import podcast_entry, podcast_group_entry

def update_podcast_entry(sender, instance=False, **kwargs):
    SearchEntry.objects.filter(obj_type='podcast', obj_id=instance.id).delete()
    entry = podcast_entry(instance)
    entry.save()

def update_podcast_group_entry(sender, instance=False, **kwargs):
    SearchEntry.objects.filter(obj_type='podcast_group', obj_id=instance.id).delete()
    entry = podcast_group_entry(instance)
    entry.save()


