from django.contrib import admin

from . import models

@admin.register(models.AuthRequest)
class AuthRequestAdmin(admin.ModelAdmin):
    list_display = ('created', 'state')
