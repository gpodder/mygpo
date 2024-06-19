import re

from django import forms
from django.utils.translation import gettext as _

from mygpo.users.models import Client

import logging

logger = logging.getLogger(__name__)

branch_coverage_UAF = []
class UserAccountForm(forms.Form):
    """
    the form that is used in the account settings.

    if one of the three password fields is set, a password change is assumed
    and the current and new passwords are checked.
    """

    email = forms.EmailField(
        label=_("E-Mail address"),
        widget=forms.TextInput(attrs={"class": "input input-sm form-control"}),
        required=True,
    )

    password_current = forms.CharField(
        label=_("Current password"),
        widget=forms.PasswordInput(
            render_value=False, attrs={"class": "input input-sm form-control"}
        ),
        required=False,
    )

    password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(
            render_value=False, attrs={"class": "input input-sm form-control"}
        ),
        required=False,
    )

    password2 = forms.CharField(
        label=_("Confirm password"),
        widget=forms.PasswordInput(
            render_value=False, attrs={"class": "input input-sm form-control"}
        ),
        required=False,
    )

    def write_coverage(self):
        with open('/home/hussein/sep/fork/mygpo/legacy_coverage.txt', 'w') as file:
            for index, coverage in enumerate(branch_coverage_UAF):
                if coverage:
                    file.write(f"Branch {index} was taken\n")
                else:
                    file.write(f"Branch {index} was not taken\n")


    def is_valid(self):
        if not super(UserAccountForm, self).is_valid():
            return False

        pw1 = self.cleaned_data["password1"]
        pw2 = self.cleaned_data["password2"]

        if self.cleaned_data["password_current"] or pw1 or pw2:
            branch_coverage_UAF[0] = True
            if self.cleaned_data["password_current"] == "":
                branch_coverage_UAF[1] = True
                self.write_coverage()
                return False  # must give current password

            if pw1 == "":
                branch_coverage_UAF[2] = True
                self.write_coverage()
                return False  # cant set empty password

            if pw1 != pw2:
                branch_coverage_UAF[3] = True
                self.write_coverage()
                return False  # 5must confirm password

        self.write_coverage()
        return True

class ProfileForm(forms.Form):
    twitter = forms.CharField(
        label=_("Twitter"),
        widget=forms.TextInput(attrs={"class": "input input-sm form-control"}),
        required=False,
    )

    about = forms.CharField(
        label=_("A few words about you"),
        required=False,
        widget=forms.Textarea(attrs={"class": "input input-sm form-control"}),
        help_text="You can use Markdown",
    )


class DeviceForm(forms.Form):
    """
    form for editing device information by a user.
    """

    name = forms.CharField(
        max_length=100,
        label=_("Name"),
        widget=forms.TextInput(
            attrs={"class": "input input-sm form-control", "placeholder": "Device Name"}
        ),
    )
    type = forms.ChoiceField(
        choices=Client.TYPES,
        label=_("Type"),
        widget=forms.Select(attrs={"class": "input input-sm form-control"}),
    )
    uid = forms.CharField(
        max_length=50,
        label=_("Device ID"),
        widget=forms.TextInput(
            attrs={
                "class": "input input-sm form-control",
                "placeholder": _("ID on device"),
            }
        ),
    )


class PrivacyForm(forms.Form):
    """
    Form for editing the privacy settings for a subscription. It is shown on a
    podcast page if the current user is subscribed to the podcast.
    """

    public = forms.BooleanField(
        required=False, label=_("Share this subscription with other users (public)")
    )


class SyncForm(forms.Form):
    """
    Form that is used to select either a single devices or a device group.
    """

    targets = forms.CharField(
        widget=forms.Select(attrs={"class": "input input-sm form-control"})
    )

    def set_targets(self, sync_targets, label=""):
        targets = list(map(self.sync_target_choice, sync_targets))
        self.fields["targets"] = forms.ChoiceField(choices=targets, label=label)

    def sync_target_choice(self, target):
        """
        returns a list of tuples that can be used as choices for a ChoiceField.
        the first item in each tuple is a letter identifying the type of the
        sync-target - either d for a Device, or g for a SyncGroup. This letter
        is followed by the id of the target.
        The second item in each tuple is the string-representation of the #
        target.
        """

        if isinstance(target, Client):
            return (target.uid, target.name)

        elif isinstance(target, list):
            return (target[0].uid, ", ".join(d.name for d in target))

    def get_target(self):
        """
        returns the target (device or device group) that has been selected
        in the form.
        """
        if not self.is_valid():
            logger.warning("no target given in SyncForm")
            raise ValueError(_("No device selected"))

        target = self.cleaned_data["targets"]
        return target


class ResendActivationForm(forms.Form):
    username = forms.CharField(
        max_length=100, label=_("Please enter your username"), required=False
    )

    email = forms.CharField(
        max_length=100,
        label=_("or the email address used while registering"),
        required=False,
    )


class RestorePasswordForm(forms.Form):
    username = forms.CharField(max_length=100, label=_("Username"), required=False)

    email = forms.CharField(max_length=100, label=_("E-Mail address"), required=False)
