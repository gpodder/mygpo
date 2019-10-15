from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from mygpo.users.models import UserProfile, Client, SyncGroup

# Define an inline admin descriptor for the UserProfile model
# which acts a bit like a singleton
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'


# Define a new User admin
class UserAdmin(UserAdmin):
    inlines = (UserProfileInline,)

    list_display = (
        'username',
        'email',
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
        'last_login',
    )


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """ Admin page for clients """

    # configuration for the list view
    list_display = ('name', 'user', 'uid', 'type')

    # fetch the client's user for the fields in list_display
    list_select_related = ('user',)

    list_filter = ('type',)
    search_fields = ('name', 'uid', 'user__username')

    raw_id_fields = ('user',)

    show_full_result_count = False


@admin.register(SyncGroup)
class SyncGroupAdmin(admin.ModelAdmin):
    """ Admin page for SyncGroups """

    list_display = ('user', 'num_clients')

    def num_clients(self, group):
        """ Numer of clients that belong to this group """
        return Client.objects.filter(sync_group=group).count()

    show_full_result_count = False
