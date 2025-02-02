import uuid

from django.db import transaction, IntegrityError

from mygpo.users.settings import STORE_UA
from mygpo.users.models import Client

import logging

logger = logging.getLogger(__name__)


def get_device(user, uid, user_agent, undelete=True):
    """
    Loads or creates the device indicated by user, uid.

    If the device has been deleted and undelete=True, it is undeleted.
    """

    store_ua = user.profile.settings.get_wksetting(STORE_UA)

    # list of fields to update -- empty list = no update
    update_fields = []
    new_client = False

    with transaction.atomic():
        try:
            client = Client.objects.get(user=user, uid=uid)
        except Client.DoesNotExist:
            client = Client(id=uuid.uuid1(), user=user, uid=uid)
            client.clean_fields()
            client.clean()
            new_client = True

    if client.deleted and undelete:
        client.deleted = False
        update_fields.append("deleted")

    if store_ua and user_agent and client.user_agent != user_agent:
        client.user_agent = user_agent
        update_fields.append("user_agent")

    if new_client:
        client.save()
    elif update_fields:
        client.save(update_fields=update_fields)

    return client
