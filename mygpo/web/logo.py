import os.path
import io
import requests
import hashlib
import socket
import struct

from PIL import Image

from django.urls import reverse
from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.http import last_modified
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.storage import FileSystemStorage

from mygpo.utils import file_hash

import logging

logger = logging.getLogger(__name__)

# Use Django's File Storage API to access podcast logos. This could be swapped
# out for another storage implementation (eg for storing to Amazon S3)
# https://docs.djangoproject.com/en/1.11/ref/files/storage/
LOGO_STORAGE = FileSystemStorage(location=settings.MEDIA_ROOT)


def _last_modified(request, size, prefix, filename):

    target = os.path.join("logo", str(size), prefix, filename)

    try:
        return LOGO_STORAGE.get_modified_time(target)

    except (FileNotFoundError, NotImplementedError):
        return None


class CoverArt(View):
    def __init__(self):
        self.storage = LOGO_STORAGE

    @method_decorator(last_modified(_last_modified))
    def get(self, request, size, prefix, filename):

        size = int(size)

        prefix = get_prefix(filename)
        target = self.get_thumbnail_path(size, prefix, filename)
        original = self.get_original_path(prefix, filename)

        if self.storage.exists(target):
            return self.send_file(target)

        if not self.storage.exists(original):
            logger.warning("Original cover {} not found".format(original))
            raise Http404("Cover Art not available" + original)

        try:
            fp = self.storage.open(original, "rb")
            im = Image.open(fp)
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGBA")
        except IOError as ioe:
            logger.warning("Cover file {} cannot be opened: {}".format(original, ioe))
            raise Http404("Cannot open cover file") from ioe

        try:
            im.thumbnail((size, size), Image.ANTIALIAS)
            resized = im
        except (struct.error, IOError, IndexError) as ex:
            # raised when trying to read an interlaced PNG;
            logger.warning("Could not create thumbnail: %s", str(ex))

            # we use the original instead
            return self.send_file(original)

        sio = io.BytesIO()

        try:
            resized.save(
                sio,
                "JPEG" if im.mode == "RGB" else "PNG",
                optimize=True,
                progression=True,
                quality=80,
            )
        except IOError as ex:
            return self.send_file(original)
        finally:
            fp.close()

        self.storage.save(target, sio)

        return self.send_file(target)

    @staticmethod
    def get_thumbnail_path(size, prefix, filename):
        return os.path.join("logo", str(size), prefix, filename)

    @staticmethod
    def get_dir(filename):
        return os.path.dirname(filename)

    @staticmethod
    def remove_existing_thumbnails(prefix, filename):
        dirs, _files = LOGO_STORAGE.listdir("logo")  # TODO: cache list of sizes
        for size in dirs:
            if size == "original":
                continue

            path = os.path.join("logo", size, prefix, filename)
            logger.info("Removing {}".format(path))
            LOGO_STORAGE.delete(path)

    @staticmethod
    def get_original_path(prefix, filename):
        return os.path.join("logo", "original", prefix, filename)

    def send_file(self, filename):
        return HttpResponseRedirect(LOGO_STORAGE.url(filename))

    @classmethod
    def save_podcast_logo(cls, cover_art_url):
        if not cover_art_url:
            return

        try:
            image_sha1 = hashlib.sha1(cover_art_url.encode("utf-8")).hexdigest()
            prefix = get_prefix(image_sha1)

            filename = cls.get_original_path(prefix, image_sha1)

            # get hash of existing file
            if LOGO_STORAGE.exists(filename):
                with LOGO_STORAGE.open(filename, "rb") as f:
                    old_hash = file_hash(f).digest()
            else:
                old_hash = ""

            logger.info("Logo {}, saving to {}".format(cover_art_url, filename))

            # save new cover art
            LOGO_STORAGE.delete(filename)
            source = io.BytesIO(requests.get(cover_art_url).content)
            LOGO_STORAGE.save(filename, source)

            # get hash of new file
            with LOGO_STORAGE.open(filename, "rb") as f:
                new_hash = file_hash(f).digest()

            # remove thumbnails if cover changed
            if old_hash != new_hash:
                logger.info("Removing thumbnails")
                cls.remove_existing_thumbnails(prefix, filename)

            return cover_art_url

        except (
            ValueError,
            requests.exceptions.RequestException,
            socket.error,
            IOError,
        ) as e:
            logger.warning("Exception while updating podcast logo: %s", str(e))


def get_prefix(filename):
    return filename[:3]


def get_logo_url(podcast, size):
    """Return the logo URL for the podcast

    The logo either comes from the media storage (see CoverArt) or from the
    default logos in the static storage.
    """

    if podcast.logo_url:
        filename = hashlib.sha1(podcast.logo_url.encode("utf-8")).hexdigest()
        return reverse("logo", args=[size, get_prefix(filename), filename])

    else:
        filename = "podcast-%d.png" % (hash(podcast.title) % 5,)
        return staticfiles_storage.url("logo/{0}".format(filename))
