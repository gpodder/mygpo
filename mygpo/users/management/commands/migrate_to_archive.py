import json
import os
import shutil
import subprocess
import sys

from datetime import datetime
from functools import wraps
from time import perf_counter
from uuid import UUID, uuid4

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from django.db.utils import IntegrityError

from mygpo.users.models import UserArchive


def timed(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        before = perf_counter()
        ret = f(*args, **kwds)
        print("D: run %s in %.1fs" % (f.__qualname__, (perf_counter() - before)))

    return wrapper


RETRY_UUID_NON_UNIQUE = 3


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
                for i in range(RETRY_UUID_NON_UNIQUE):
                    try:
                        a = UserArchive(
                            id=uuid4(),
                            user=user,
                            date=user.profile.archived_date,
                            path=user.profile.archive_path,
                        )
                        a.save(force_insert=True)
                        print(
                            f"Created {user.username} date {user.profile.archived_date} path {user.profile.archive_path}"
                        )
                        break
                    except IntegrityError:
                        if i == RETRY_UUID_NON_UNIQUE - 1:
                            raise
