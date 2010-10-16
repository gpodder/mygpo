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

from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden
from django.template import RequestContext
from mygpo.api.models import Device, EpisodeAction, SubscriptionAction
from mygpo.data.models import BackendSubscription, Listener
from mygpo.web.forms import DeviceForm, SyncForm
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from mygpo.log import log
from mygpo.api import simple
from mygpo.decorators import manual_gc, allowed_methods


@manual_gc
@login_required
def overview(request):
    devices = Device.objects.filter(user=request.user,deleted=False).order_by('sync_group')
    deleted_devices = Device.objects.filter(user=request.user,deleted=True)

    return render_to_response('devicelist.html', {
        'devices': devices,
        'deleted_devices': deleted_devices,
    }, context_instance=RequestContext(request))


@manual_gc
@login_required
def show(request, device_id, error_message=None):
    device = Device.objects.get(pk=device_id, user=request.user)

    if device.user != request.user:
        return HttpResponseForbidden(_('You are not allowed to access this device'))

    subscriptions = device.get_subscriptions()
    synced_with = list(device.sync_group.devices()) if device.sync_group else []
    if device in synced_with: synced_with.remove(device)
    sync_form = SyncForm()
    sync_form.set_targets(device.sync_targets(), _('Synchronize with the following devices'))

    return render_to_response('device.html', {
        'device': device,
        'sync_form': sync_form,
        'error_message': error_message,
        'subscriptions': subscriptions,
        'synced_with': synced_with,
        'has_sync_targets': len(device.sync_targets()) > 0
    }, context_instance=RequestContext(request))


@login_required
@allowed_methods(['GET', 'POST'])
def edit(request, device_id=None):
    if device_id:
        device = get_object_or_404(Device, id=device_id, user=request.user)
    else:
        device = Device(name=_('New Device'), uid=_('new-device'), user=request.user)

    success = False
    error_message = ''

    if request.method == 'POST':
        device_form = DeviceForm(request.POST)

        if device_form.is_valid():
            device.name = device_form.cleaned_data['name']
            device.type = device_form.cleaned_data['type']
            device.uid  = device_form.cleaned_data['uid']
            try:
                device.save()
                success = True

                if not device_id:
                    return HttpResponseRedirect(reverse('device', args=[device.id]))

            except IntegrityError, ie:
                error_message = _('You can\'t use the same Device ID for two devices.')

    else:
        device_form = DeviceForm({
            'name': device.name,
            'type': device.type,
            'uid' : device.uid
            })

    template = 'device-edit.html' if device_id else 'device-create.html'
    return render_to_response(template, {
        'device': device,
        'device_form': device_form,
        'success': success,
        'error_message': error_message,
    }, context_instance=RequestContext(request))


@login_required
def upload_opml(request, device_id):
    device = get_object_or_404(Device, id=device_id, user=request.user)
    opml = request.FILES['opml'].read()
    subscriptions = simple.parse_subscription(opml, 'opml')
    simple.set_subscriptions(subscriptions, request.user, device.uid)
    return HttpResponseRedirect(reverse('device', args=[device.id]))


@manual_gc
@login_required
def opml(request, device_id):
    device = get_object_or_404(Device, id=device_id, user=request.user)

    response = simple.format_podcast_list(simple.get_subscriptions(request.user, device.uid), 'opml', request.user.username)
    response['Content-Disposition'] = 'attachment; filename=%s.opml' % device.uid
    return response


@login_required
def symbian_opml(request, device_id):
    device = get_object_or_404(Device, id=device_id, user=request.user)

    subscriptions = simple.get_subscriptions(request.user, device.uid)

    for p in subscriptions:
        p.description = (p.title or '') + '\n' + (p.description or '')

    response = simple.format_podcast_list(subscriptions, 'opml', request.user.username)
    response['Content-Disposition'] = 'attachment; filename=%s.opml' % device.uid
    return response


@manual_gc
@login_required
@allowed_methods(['POST'])
def delete(request, device_id):
    device = Device.objects.get(pk=device_id)
    device.deleted = True
    device.save()

    return HttpResponseRedirect('/devices/')


def delete_permanently(request, device_id):

    device = get_object_or_404(Device, pk=device_id, user=request.user)

    SubscriptionAction.objects.filter(device=device).delete()
    EpisodeAction.objects.filter(device=device).delete()
    BackendSubscription.objects.filter(device=device).delete()
    Listener.objects.filter(device=device).delete()
    device.delete()

    return HttpResponseRedirect('/devices/')

@manual_gc
@login_required
def undelete(request, device_id):
    device = get_object_or_404(Device, pk=device_id, user=request.user)

    device.deleted = False
    device.save()

    return HttpResponseRedirect('/device/%s' % device.id)


@manual_gc
@login_required
@allowed_methods(['POST'])
def sync(request, device_id):
    form = SyncForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest('invalid')

    try:
        target = form.get_target()

        device = Device.objects.get(pk=device_id)
        device.sync_with(target)

    except ValueError, e:
        log('error while syncing device %s: %s' % (device_id, e))

    return HttpResponseRedirect('/device/%s' % device_id)


@manual_gc
@login_required
@allowed_methods(['GET'])
def unsync(request, device_id):
    dev = Device.objects.get(pk=device_id)

    try:
        dev.unsync()
    except ValueError, e:
        return show(request, device_id, e)

    return HttpResponseRedirect('/device/%s' % device_id)


from mygpo.web import views
history = views.history

