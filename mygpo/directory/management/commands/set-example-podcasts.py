from datetime import datetime
import fileinput

from django.core.management.base import BaseCommand

from couchdbkit.exceptions import ResourceNotFound

from mygpo.core.models import Podcast
from mygpo.directory.models import ExamplePodcasts


EXAMPLES_DOCID = 'example_podcasts'

class Command(BaseCommand):

    def handle(self, *args, **options):

        urls = list(fileinput.input(args))

        try:
            examples = ExamplePodcasts.get(EXAMPLES_DOCID)
        except ResourceNotFound:
            examples = ExamplePodcasts()
            examples._id = EXAMPLES_DOCID

        podcasts = filter(None, [Podcast.for_url(url) for url in urls])
        examples.podcast_ids = [podcast.get_id() for podcast in podcasts]
        examples.updated = datetime.utcnow()
        examples.save()
