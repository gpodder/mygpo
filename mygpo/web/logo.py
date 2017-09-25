import os.path
import io
from datetime import datetime
from glob import glob
import errno
import hashlib
import struct

from PIL import Image, ImageDraw

from django.urls import reverse
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseNotFound
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.http import last_modified

import logging
logger = logging.getLogger(__name__)

LOGO_DIR = os.path.join(settings.BASE_DIR, '..', 'htdocs', 'media', 'logo')


def _last_modified(request, size, prefix, filename):

    target = os.path.join(LOGO_DIR, size, prefix, filename)

    try:
        return datetime.fromtimestamp(os.path.getmtime(target))

    except OSError:
        return None


class CoverArt(View):

    @method_decorator(last_modified(_last_modified))
    def get(self, request, size, prefix, filename):

        size = int(size)

        target = self.get_thumbnail(size, prefix, filename)
        original = self.get_original(prefix, filename)

        if os.path.exists(target):
            return self.send_file(target)

        if not os.path.exists(original):
            raise Http404('Cover Art not available' + original)

        target_dir = self.get_dir(target)

        try:
            im = Image.open(original)
            if im.mode not in ('RGB', 'RGBA'):
                im = im.convert('RGB')
        except IOError:
            raise Http404('Cannot open cover file')

        try:
            im.thumbnail((size, size), Image.ANTIALIAS)
            resized = im
        except (struct.error, IOError, IndexError) as ex:
            # raised when trying to read an interlaced PNG;
            logger.warn('Could not create thumbnail: %s', str(ex))

            # we use the original instead
            return self.send_file(original)

        # If it's a RGBA image, composite it onto a white background for JPEG
        if resized.mode == 'RGBA':
            background = Image.new('RGB', resized.size)
            draw = ImageDraw.Draw(background)
            draw.rectangle((-1, -1, resized.size[0]+1, resized.size[1]+1),
                           fill=(255, 255, 255))
            del draw
            resized = Image.composite(resized, background, resized)

        sio = io.BytesIO()

        try:
            resized.save(sio, 'JPEG', optimize=True, progression=True,
                         quality=80)
        except IOError as ex:
            return self.send_file(original)

        s = sio.getvalue()

        fp = open(target, 'wb')
        fp.write(s)
        fp.close()

        return self.send_file(target)

    # the length of the prefix is defined here and in web/urls.py
    @staticmethod
    def get_prefix(filename):
        return filename[:3]

    @staticmethod
    def get_thumbnail(size, prefix, filename):
        return os.path.join(LOGO_DIR, str(size), prefix, filename)

    @staticmethod
    def get_existing_thumbnails(prefix, filename):
        files = glob(os.path.join(LOGO_DIR, '*', prefix, filename))
        return [f for f in files if 'original' not in f]

    @staticmethod
    def get_original(prefix, filename):
        return os.path.join(LOGO_DIR, 'original', prefix, filename)

    @staticmethod
    def get_dir(filename):
        path = os.path.dirname(filename)
        try:
            os.makedirs(path)

        except OSError as ose:
            if ose.errno != errno.EEXIST:
                raise

        return path

    def send_file(self, filename):
        try:
            f = open(filename, 'rb')
        except IOError:
            return HttpResponseNotFound()

        resp = HttpResponse(content_type='image/jpeg')
        resp.status_code = 200
        resp.write(f.read())
        return resp


def get_logo_url(podcast, size):
    """ Return the logo URL for the podcast """

    if podcast.logo_url:
        filename = hashlib.sha1(podcast.logo_url.encode('utf-8')).hexdigest()
    else:
        filename = 'podcast-%d.png' % (hash(podcast.title) % 5, )

    prefix = CoverArt.get_prefix(filename)

    return reverse('logo', args=[size, prefix, filename])
