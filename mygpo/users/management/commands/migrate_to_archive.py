import json
import os
import shutil
import subprocess
import sys

from datetime import datetime
from uuid import uuid4

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from mygpo.users.models import UserArchive
from mygpo.utils import timed


class Command(BaseCommand):
    """
    Convert from archived_date to UserArchive
    """

    @timed
    def handle(
        self,
        *args,
        **options,
    ):

        User = get_user_model()
        for user in User.objects.filter(profile__archived_date__isnull=False):
            if user.userarchive_set.filter(date=user.profile.archived_date).exists():
                print(f"Skipping {user.username} date {user.profile.archive_path}")
            else:
                a = UserArchive(
                    id=uuid4(),
                    user=user,
                    date=user.profile.archived_date,
                    path=user.profile.archive_path,
                )
                a.save_with_id_retry(a)
                print(
                    f"Created {user.username} date {user.profile.archived_date} path {user.profile.archive_path}"
                )
