"""
psql -h 172.17.0.2 -p 5014 -U postgres mygpo  -X -A -w -t -c "select username from auth_user where last_login < '2024-01-01' and id > 201 order by id asc;" | xargs  -I '{}' envdir envs/dev python manage.py archive '{}' /tmp/'{}'.archive --archive '/run/media/elelay/HDD/mygpo/archive/{}.tar.zstd' 2>&1 | tee /run/media/elelay/HDD/mygpo/archive/archive.log
"""

import os
from datetime import datetime
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from mygpo.users.models import UserArchive
from mygpo.users.tasks import UserArchiver
from mygpo.utils import timed


class Command(BaseCommand):
    """
    Create an archive of all user content.

    The user is specified by its user id.
    """

    def add_arguments(self, parser):
        parser.add_argument("username_or_id", type=str)
        parser.add_argument("output_dir", type=str)
        parser.add_argument("--archive", type=str)
        parser.add_argument("--is-username", type=bool, default=False)
        parser.add_argument("--keep-output-dir", type=bool, default=False)
        parser.add_argument("--and-delete", type=bool, default=False)

    @timed
    def handle(
        self,
        *args,
        username_or_id,
        is_username,
        output_dir,
        keep_output_dir,
        and_delete,
        **options,
    ):

        User = get_user_model()
        if is_username:
            user = User.objects.get(username=username_or_id)
        else:
            user = User.objects.get(id=int(username_or_id))
        if not user:
            raise CommandError(f"User {username_or_id} does not exist", returncode=-1)

        if not user.is_active and user.profile.archived_date is not None:
            raise CommandError(
                f"User {username_or_id} already archived on {user.profile.archived_date}",
                returncode=1,
            )

        if options.get("archive"):
            archive_dest = options["archive"]
        else:
            archive_dest = os.path.join(
                settings.ARCHIVE_ROOT,
                f"{user.username}-{user.id}.tar.zst" % (user.username, user.id),
            )

        if not os.path.exists(os.path.dirname(archive_dest)):
            raise CommandError(
                f"archive {archive_dest} parent directory doesnt exist", returncode=1
            )

        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        elif not os.path.exists(os.path.join(output_dir, "meta.json")):
            raise CommandError(
                "output_dir exists and doesn't contain meta.json", returncode=1
            )

        print(f"archiving user {user.username} (id={user.id})")
        archive = UserArchive(id=uuid4(), user=user, date=datetime.now())
        archive.save_with_id_retry()

        archiver = UserArchiver(
            archive=archive, output_dir=output_dir, archive_dest=archive_dest
        )
        archiver.archive(keep_output_dir=keep_output_dir, and_delete=and_delete)

        archive.path = archive_dest
        archive.save()
