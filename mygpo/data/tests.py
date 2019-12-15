import re
import json

from django.test import TestCase

from . import flickr

import responses


MEDIUM_URL = 'https://farm6.staticflickr.com/5001/1246644888_36863b0856.jpg'

API_RESPONSE = {
    'stat': 'ok',
    'sizes': {
        'canblog': 0,
        'size': [
            {
                'source': 'https://farm6.staticflickr.com/5001/1234533888_45673b0856_s.jpg',
                'url': 'https://www.flickr.com/photos/someuser/135643888/sizes/sq/',
                'media': 'photo',
                'height': 75,
                'width': 75,
                'label': 'Square',
            },
            {
                'source': MEDIUM_URL,
                'url': 'https://www.flickr.com/photos/someuser/3465234888/sizes/m/',
                'media': 'photo',
                'height': '500',
                'width': '333',
                'label': 'Medium',
            },
        ],
        'candownload': 1,
        'canprint': 0,
    },
}

FLICKR_URL = re.compile(
    'https://api.flickr.com/services/rest/\?method=flickr.photos.getSizes&api_key=.*photo_id=.*&format=json&nojsoncallback=1'
)


class FlickrTests(TestCase):
    def test_get_sizes(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET, FLICKR_URL, status=200, body=json.dumps(API_RESPONSE)
            )

            sizes = flickr.get_photo_sizes('1235123123')

        self.assertEqual(sizes, API_RESPONSE['sizes']['size'])

    def test_display_image(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET, FLICKR_URL, status=200, body=json.dumps(API_RESPONSE)
            )

            disp_photo = flickr.get_display_photo(
                'https://farm9.staticflickr.com/8747/12346789012_bf1e234567_b.jpg'
            )

        self.assertEqual(disp_photo, MEDIUM_URL)
