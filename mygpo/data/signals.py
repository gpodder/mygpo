from django.db.models.signals import post_save, pre_delete
from mygpo.data.models import DirectoryEntry
from mygpo.data.directory import get_source_weights, get_weighted_tags, get_weighted_group_tags


def update_podcast_tag_entry(sender, instance=False, **kwargs):

    if not instance:
        return

    source_weights = get_source_weights()

    if not instance.podcast.group:
        DirectoryEntry.objects.filter(podcast=instance.podcast).delete()

        for tag, weight in get_weighted_tags(instance.podcast, source_weights).iteritems():
            if weight == 0:
                continue

            DirectoryEntry.objects.create(podcast=instance.podcast, tag=tag, ranking=weight)

    else:
        DirectoryEntry.objects.filter(podcast_group=instance.podcast.group).delete()

        for tag, weight in get_weighted_group_tags(instance.podcast.group, source_weights).iteritems():
            if weight == 0:
                continue

            DirectoryEntry.objects.create(podcast_group=instance.podcast.group, tag=tag, ranking=weight)

