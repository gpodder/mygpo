import json
import re
import requests

from django.conf import settings

import logging

logger = logging.getLogger(__name__)


GET_SIZES_TEMPLATE = "https://api.flickr.com/services/rest/?method=flickr.photos.getSizes&api_key={api_key}&photo_id={photo_id}&format=json&nojsoncallback=1"


def get_photo_sizes(photo_id):
    """Returns available sizes for the photo with the given ID

    Returns a list of dicts containing the following keys
    * source
    * url
    * media
    * height
    * width
    * label
    """

    api_key = settings.FLICKR_API_KEY
    url = GET_SIZES_TEMPLATE.format(api_key=api_key, photo_id=photo_id)

    try:
        resp = requests.get(url)
    except requests.exceptions.RequestException as e:
        logger.warning("Retrieving Flickr photo sizes failed: %s", str(e))
        return []

    try:
        resp_obj = resp.json()
    except json.JSONDecodeError as jde:
        return []

    try:
        return resp_obj["sizes"]["size"]
    except KeyError:
        return []


def get_photo_id(url):
    """Returns the Photo ID for a Photo URL

    >>> get_photo_id('https://farm9.staticflickr.com/8747/12346789012_bf1e234567_b.jpg')
    '12346789012'

    >>> get_photo_id('https://www.flickr.com/photos/someuser/12345678901/')
    '12345678901'

    """

    photo_id_re = [
        "http://.*flickr.com/[^/]+/([^_]+)_.*",
        "https://.*staticflickr.com/[^/]+/([^_]+)_.*",
        "https?://.*flickr.com/photos/[^/]+/([^/]+).*",
    ]

    for regex in photo_id_re:
        match = re.match(regex, url)
        if match:
            return match.group(1)


def is_flickr_image(url):
    """Returns True if the URL represents a Flickr images

    >>> is_flickr_image('https://farm9.staticflickr.com/8747/12346789012_bf1e234567_b.jpg')
    True

    >>> is_flickr_image('http://www.example.com/podcast.mp3')
    False

    >>> is_flickr_image(None)
    False
    """

    if url is None:
        return False
    return bool(re.search(r"flickr\.com.*\.(jpg|jpeg|png|gif)", url))


def get_display_photo(url, label="Medium"):
    photo_id = get_photo_id(url)
    sizes = get_photo_sizes(photo_id)
    for s in sizes:
        if s["label"] == label:
            return s["source"]

    return url
