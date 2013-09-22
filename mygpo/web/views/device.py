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

from functools import wraps
from xml.parsers.expat import ExpatError

from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseBadRequest, \
        HttpResponseNotFound
from django.contrib import messages
from mygpo.web.forms import DeviceForm, SyncForm
from mygpo.web.utils import symbian_opml_changes
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache, cache_control

from restkit.errors import Unauthorized

from mygpo.api import simple
from mygpo.decorators import allowed_methods, repeat_on_conflict
from mygpo.users.models import Device, DeviceUIDException, \
     DeviceDoesNotExist
from mygpo.users.tasks import sync_user, set_device_task_state
from mygpo.db.couchdb.podcast_state import podcast_states_for_device, \
         remove_device_from_podcast_state
from mygpo.db.couchdb.user import set_device_deleted, unsync_device, set_device


@vary_on_cookie
@cache_control(private=True)
@login_required
def overview(request):

    device_groups = request.user.get_grouped_devices()
    deleted_devices = request.user.inactive_devices

    return render(request, 'devicelist.html', {
        'device_groups': device_groups,
        'deleted_devices': deleted_devices,
    })



def device_decorator(f):
    @login_required
    @vary_on_cookie
    @cache_control(private=True)
    @wraps(f)
    def _decorator(request, uid, *args, **kwargs):

        try:
            device = request.user.get_device_by_uid(uid, only_active=False)

        except DeviceDoesNotExist as e:
            return HttpResponseNotFound(str(e))

        return f(request, device, *args, **kwargs)

    return _decorator



@login_required
@device_decorator
def show(request, device):

    request.user.sync_group(device)

    subscriptions = list(device.get_subscribed_podcasts())
    synced_with = request.user.get_synced(device)

    sync_targets = list(request.user.get_sync_targets(device))
    sync_form = SyncForm()
    sync_form.set_targets(sync_targets,
            _('Synchronize with the following devices'))

    return render(request, 'device.html', {
        'device': device,
        'sync_form': sync_form,
        'subscriptions': subscriptions,
        'synced_with': synced_with,
        'has_sync_targets': len(sync_targets) > 0,
    })


@login_required
@never_cache
@allowed_methods(['POST'])
def create(request):
    device_form = DeviceForm(request.POST)

    if not device_form.is_valid():

        messages.error(request, _('Please fill out all fields.'))

        return HttpResponseRedirect(reverse('device-edit-new'))


    device = Device()
    device.name = device_form.cleaned_data['name']
    device.type = device_form.cleaned_data['type']
    device.uid  = device_form.cleaned_data['uid'].replace(' ', '-')
    try:
        set_device(request.user, device)
        messages.success(request, _('Device saved'))

    except DeviceUIDException as e:
        messages.error(request, _(unicode(e)))

        return render(request, 'device-create.html', {
            'device': device,
            'device_form': device_form,
        })

    except Unauthorized:
        messages.error(request, _("You can't use the same Device "
                   "ID for two devices."))

        return render(request, 'device-create.html', {
            'device': device,
            'device_form': device_form,
        })


    return HttpResponseRedirect(reverse('device-edit', args=[device.uid]))



@device_decorator
@login_required
@allowed_methods(['POST'])
def update(request, device):
    device_form = DeviceForm(request.POST)

    uid = device.uid

    if device_form.is_valid():

        device.name = device_form.cleaned_data['name']
        device.type = device_form.cleaned_data['type']
        device.uid  = device_form.cleaned_data['uid'].replace(' ', '-')
        try:
            set_device(request.user, device)
            messages.success(request, _('Device updated'))
            uid = device.uid  # accept the new UID after rest has succeeded

        except DeviceUIDException as e:
            messages.error(request, _(str(e)))

        except Unauthorized as u:
            messages.error(request, _("You can't use the same Device "
                       "ID for two devices."))

    return HttpResponseRedirect(reverse('device-edit', args=[uid]))


@login_required
@vary_on_cookie
@cache_control(private=True)
@allowed_methods(['GET'])
def edit_new(request):

    device = Device()

    device_form = DeviceForm({
        'name': device.name,
        'type': device.type,
        'uid': device.uid
        })

    return render(request, 'device-create.html', {
        'device': device,
        'device_form': device_form,
    })




@device_decorator
@login_required
@allowed_methods(['GET'])
def edit(request, device):

    device_form = DeviceForm({
        'name': device.name,
        'type': device.type,
        'uid': device.uid
        })

    synced_with = request.user.get_synced(device)

    sync_targets = list(request.user.get_sync_targets(device))
    sync_form = SyncForm()
    sync_form.set_targets(sync_targets,
            _('Synchronize with the following devices'))

    return render(request, 'device-edit.html', {
        'device': device,
        'device_form': device_form,
        'sync_form': sync_form,
        'synced_with': synced_with,
        'has_sync_targets': len(sync_targets) > 0,
    })


@device_decorator
@login_required
def upload_opml(request, device):

    if not 'opml' in request.FILES:
        return HttpResponseRedirect(reverse('device-edit', args=[device.uid]))

    opml = request.FILES['opml'].read()

    try:
        subscriptions = simple.parse_subscription(opml, 'opml')
        simple.set_subscriptions(subscriptions, request.user, device.uid, None)

    except ExpatError as ee:
        msg = _('Could not upload subscriptions: {err}').format(err=str(ee))
        messages.error(request, msg)
        return HttpResponseRedirect(reverse('device-edit', args=[device.uid]))

    return HttpResponseRedirect(reverse('device', args=[device.uid]))


@device_decorator
@login_required
def opml(request, device):
    response = simple.format_podcast_list(simple.get_subscriptions(request.user, device.uid), 'opml', request.user.username)
    response['Content-Disposition'] = 'attachment; filename=%s.opml' % device.uid
    return response


@device_decorator
@login_required
def symbian_opml(request, device):
    subscriptions = simple.get_subscriptions(request.user, device.uid)
    subscriptions = map(symbian_opml_changes, subscriptions)

    response = simple.format_podcast_list(subscriptions, 'opml', request.user.username)
    response['Content-Disposition'] = 'attachment; filename=%s.opml' % device.uid
    return response


@device_decorator
@login_required
@allowed_methods(['POST'])
def delete(request, device):
    user = request.user
    unsync_device(user, device)
    set_device_deleted(user, device, True)
    set_device_task_state.delay(user)
    return HttpResponseRedirect(reverse('devices'))


@login_required
@device_decorator
def delete_permanently(request, device):

    states = podcast_states_for_device(device.id)
    for state in states:
        remove_device_from_podcast_state(state, device)

    @repeat_on_conflict(['user'])
    def _remove(user, device):
        user.remove_device(device)
        user.save()

    _remove(user=request.user, device=device)

    return HttpResponseRedirect(reverse('devices'))

@device_decorator
@login_required
def undelete(request, device):
    user = request.user
    set_device_deleted(user, device, False)
    set_device_task_state.delay(user)
    return HttpResponseRedirect(reverse('device', args=[device.uid]))


@device_decorator
@login_required
@allowed_methods(['POST'])
def sync(request, device):

    form = SyncForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest('invalid')


    @repeat_on_conflict(['user'])
    def do_sync(user, device, sync_target):
        user.sync_devices(device, sync_target)
        user.save()


    try:
        target_uid = form.get_target()
        sync_target = request.user.get_device_by_uid(target_uid)
        do_sync(user=request.user, device=device, sync_target=sync_target)

    except DeviceDoesNotExist as e:
        messages.error(request, str(e))

    sync_user.delay(request.user)

    return HttpResponseRedirect(reverse('device', args=[device.uid]))


@device_decorator
@login_required
@allowed_methods(['GET'])
def unsync(request, device):

    @repeat_on_conflict(['user'])
    def do_unsync(user, device):
        user.unsync_device(device)
        user.save()

    try:
        do_unsync(user=request.user, device=device)

    except ValueError, e:
        messages.error(request, 'Could not unsync the device: {err}'.format(
                    err=str(e)))

    return HttpResponseRedirect(reverse('device', args=[device.uid]))


from mygpo.web import views
history = views.history
