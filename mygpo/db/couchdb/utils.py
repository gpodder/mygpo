#
# This file is part of my.gpodder.org.
#
# my.gpodder.org is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# my.gpodder.org is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with my.gpodder.org. If not, see <http://www.gnu.org/licenses/>.
#

import os.path

from couchdbkit.loaders import FileSystemDocsLoader
from couchdbkit.ext.django import loading

from django.conf import settings

import logging
logger = logging.getLogger(__name__)


def sync_design_docs():
    """ synchronize the design docs for all databases """

    base_dir = settings.BASE_DIR

    for part, label in settings.COUCHDB_DDOC_MAPPING.items():
            path = os.path.join(base_dir, '..', 'couchdb', part, '_design')

            logger.info('syncing ddocs for "%s" from "%s"', label, path)

            db = loading.get_db(label)
            loader = FileSystemDocsLoader(path)
            loader.sync(db, verbose=True)
