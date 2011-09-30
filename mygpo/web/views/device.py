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
from django.http import HttpResponseRedirect, HttpResponseBadRequest, \
        HttpResponseForbidden, Http404
from django.template import RequestContext
from django.contrib import messages
from mygpo.web.forms import DeviceForm, SyncForm
from mygpo.web import utils
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from mygpo.log import log
from mygpo.api import simple
from mygpo.decorators import manual_gc, allowed_methods, repeat_on_conflict
from mygpo.users.models import PodcastUserState, Device
from mygpo import migrate


@manual_gc
@login_required
def overview(request):

    user = migrate.get_or_migrate_user(request.user)
    device_groups = user.get_grouped_devices()

    deleted_devices = user.inactive_devices

    return render_to_response('devicelist.html', {
        'device_groups': device_groups,
        'deleted_devices': deleted_devices,
    }, context_instance=RequestContext(request))



def device_decorator(f):
    def _decorator(request, uid, *args, **kwargs):

        user = migrate.get_or_migrate_user(request.user)
        device = user.get_device_by_uid(uid)

        if not device:
            raise Http404

        return f(request, device, *args, **kwargs)

    return _decorator



@device_decorator
@manual_gc
@login_required
def show(request, device):

    user = migrate.get_or_migrate_user(request.user)
    user.sync_group(device)

    subscriptions = list(device.get_subscribed_podcasts())
    synced_with = user.get_synced(device)

    sync_targets = list(user.get_sync_targets(device))
    sync_form = SyncForm()
    sync_form.set_targets(sync_targets,
            _('Synchronize with the following devices'))

    return render_to_response('device.html', {
        'device': device,
        'sync_form': sync_form,
        'subscriptions': subscriptions,
        'synced_with': synced_with,
        'has_sync_targets': len(sync_targets) > 0,
    }, context_instance=RequestContext(request))


@login_required
@allowed_methods(['POST'])
def create(request):
    device_form = DeviceForm(request.POST)

    user = migrate.get_or_migrate_user(request.user)

    if not device_form.is_valid():

        messages.error(request, _('Please fill out all fields.'))

        return HttpResponseRedirect(reverse('device-edit-new'))


    device = Device()
    device.name = device_form.cleaned_data['name']
    device.type = device_form.cleaned_data['type']
    device.uid  = device_form.cleaned_data['uid']
    try:
        user.set_device(device)
        user.save()
        messages.success(request, _('Device saved'))

    except IntegrityError, ie:
        messages.error(request, _("You can't use the same Device "
                   "ID for two devices."))

    return HttpResponseRedirect(reverse('device-edit', args=[device.uid]))



@device_decorator
@login_required
@allowed_methods(['POST'])
def update(request, device):
    device_form = DeviceForm(request.POST)

    user = migrate.get_or_migrate_user(request.user)

    if device_form.is_valid():
        device.name = device_form.cleaned_data['name']
        device.type = device_form.cleaned_data['type']
        device.uid  = device_form.cleaned_data['uid']
        try:
            user.set_device(device)
            user.save()
            messages.success(request, _('Device updated'))

        except IntegrityError, ie:
            messages.error(request, _("You can't use the same Device "
                       "ID for two devices."))

    return HttpResponseRedirect(reverse('device-edit', args=[device.uid]))


@login_required
@allowed_methods(['GET'])
def edit_new(request):

    device = Device()

    device_form = DeviceForm({
        'name': device.name,
        'type': device.type,
        'uid' : device.uid
        })

    return render_to_response('device-create.html', {
        'device': device,
        'device_form': device_form,
    }, context_instance=RequestContext(request))




@device_decorator
@login_required
@allowed_methods(['GET'])
def edit(request, device):

    device_form = DeviceForm({
        'name': device.name,
        'type': device.type,
        'uid' : device.uid
        })

    return render_to_response('device-edit.html', {
        'device': device,
        'device_form': device_form,
    }, context_instance=RequestContext(request))


@device_decorator
@login_required
def upload_opml(request, device):

    if not 'opml' in request.FILES:
        return HttpResponseRedirect(reverse('device-edit', args=[device.id]))

    opml = request.FILES['opml'].read()
    subscriptions = simple.parse_subscription(opml, 'opml')
    simple.set_subscriptions(subscriptions, request.user, device.uid)
    return HttpResponseRedirect(reverse('device', args=[device.id]))


@device_decorator
@manual_gc
@login_required
def opml(request, device):
    response = simple.format_podcast_list(simple.get_subscriptions(request.user, device.uid), 'opml', request.user.username)
    response['Content-Disposition'] = 'attachment; filename=%s.opml' % device.uid
    return response


@device_decorator
@login_required
def symbian_opml(request, device):
    subscriptions = simple.get_subscriptions(request.user, device.uid)
    subscriptions = map(utils.symbian_opml_changes, subscriptions)

    response = simple.format_podcast_list(subscriptions, 'opml', request.user.username)
    response['Content-Disposition'] = 'attachment; filename=%s.opml' % device.uid
    return response


@device_decorator
@manual_gc
@login_required
@allowed_methods(['POST'])
def delete(request, device):

    user = migrate.get_or_migrate_user(request.user)

    if user.is_synced(device):
        user.unsync_device(device)

    device.deleted = True
    user.set_device(device)
    user.save()

    return HttpResponseRedirect(reverse('devices'))


@device_decorator
def delete_permanently(request, device):

    @repeat_on_conflict(['state'])
    def remove_device(state, dev):
        state.remove_device(dev)
        state.save()

    states = PodcastUserState.for_device(dev.id)
    for state in states:
        remove_device(state=state, dev=device)

    device.delete()

    return HttpResponseRedirect(reverse('devices'))

@device_decorator
@manual_gc
@login_required
def undelete(request, device):

    user = migrate.get_or_migrate_user(request.user)

    device.deleted = False
    user.set_device(device)
    user.save()

    return HttpResponseRedirect(reverse('device', args=[device.uid]))


@device_decorator
@manual_gc
@login_required
@allowed_methods(['POST'])
def sync(request, device):

    user = migrate.get_or_migrate_user(request.user)

    form = SyncForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest('invalid')

    try:
        target_uid = form.get_target()

        sync_target = user.get_device_by_uid(target_uid)
        user.sync_devices(device, sync_target)
        user.save()

    except ValueError, e:
        raise
        log('error while syncing device %s: %s' % (device_id, e))

    return HttpResponseRedirect(reverse('device', args=[device.uid]))


@device_decorator
@manual_gc
@login_required
@allowed_methods(['GET'])
def unsync(request, device):
    user = migrate.get_or_migrate_user(request.user)

    try:
        user.unsync_device(device)
        user.save()

    except ValueError, e:
        messages.error(request, e)

    return HttpResponseRedirect(reverse('device', args=[device.uid]))


from mygpo.web import views
history = views.history

