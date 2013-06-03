from datetime import datetime
import os.path

from django.core.management.base import BaseCommand

from mygpo.users.models import User
from mygpo.api.advanced import update_episodes
from mygpo.core.json import json
from mygpo.utils import progress


class Command(BaseCommand):
    """Imports episode actions from a file named <userid>-<something>"""

    def handle(self, *args, **options):

        path = args[0]

        for filename in os.listdir(path):
            user_id, _ = filename.split('-', 1)
            filename = os.path.join(path, filename)
            self.import_file(user_id, filename)
            print


    def import_file(self, user_id, filename):

        progress(0, 100, filename)

        with open(filename, 'r') as f:
            actions = json.load(f)

        progress(0, len(actions), filename)

        user = User.get(user_id)

        now = datetime.now()

        batch_size = 100

        count = len(actions) / batch_size

        for low in range(0, len(actions), batch_size):
            high = low+batch_size
            batch = actions[low:high]

            update_episodes(user, batch, now, None)

            progress(high, len(actions), filename)
