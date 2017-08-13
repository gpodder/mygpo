from django.contrib import admin

from . import models


class MergeTaskEntryInline(admin.TabularInline):
    model = models.MergeTaskEntry

    fields = ['podcast', ]
    readonly_fields = ['podcast', ]


@admin.register(models.MergeTask)
class MergeTaskAdmin(admin.ModelAdmin):

    model = models.MergeTask

    readonly_fields = ['id', ]
    list_display = ['id', 'num_entries',]

    show_full_result_count = False

    inlines = [
        MergeTaskEntryInline,
    ]

    def num_entries(self, obj):
        return obj.entries.count()
