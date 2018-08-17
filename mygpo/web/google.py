from django.conf import settings


def analytics(request):
    pid = settings.GOOGLE_ANALYTICS_PROPERTY_ID
    if pid:
        return {'google_analytics_property_id': pid}
    else:
        return {}


def adsense(request):
    adclient = settings.ADSENSE_CLIENT
    if not adclient:
        return {}

    slot_bottom = settings.ADSENSE_SLOT_BOTTOM
    if not slot_bottom:
        return {}

    return {'adsense_client': adclient, 'adsense_slot_bottom': slot_bottom}
