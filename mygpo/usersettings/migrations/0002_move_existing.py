import json

from django.db import migrations


def move_podcastsettings(apps, schema_editor):

    PodcastConfig = apps.get_model("subscriptions", "PodcastConfig")
    UserSettings = apps.get_model("usersettings", "UserSettings")
    ContentType = apps.get_model('contenttypes', 'ContentType')

    for cfg in PodcastConfig.objects.all():
        if not json.loads(cfg.settings):
            continue

        setting, created = UserSettings.objects.update_or_create(
            user=cfg.user,
            # we can't get the contenttype from cfg.podcast as it would be a
            # different model
            content_type=ContentType.objects.get(app_label='podcasts', model='podcast'),
            object_id=cfg.podcast.pk,
            defaults={'settings': cfg.settings},
        )


def move_usersettings(apps, schema_editor):

    UserProfile = apps.get_model("users", "UserProfile")
    UserSettings = apps.get_model("usersettings", "UserSettings")

    for profile in UserProfile.objects.all():
        if not json.loads(profile.settings):
            continue

        setting, created = UserSettings.objects.update_or_create(
            user=profile.user,
            content_type=None,
            object_id=None,
            defaults={'settings': profile.settings},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('usersettings', '0001_initial'),
        ('subscriptions', '0002_unique_constraint'),
        ('users', '0011_syncgroup_blank'),
    ]

    operations = [
        migrations.RunPython(move_podcastsettings),
        migrations.RunPython(move_usersettings),
    ]
