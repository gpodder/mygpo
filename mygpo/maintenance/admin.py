from django.contrib import admin

from . import models


class MergeQueueEntryInline(admin.TabularInline):
    model = models.MergeQueueEntry

    fields = ['podcast', ]
    readonly_fields = ['podcast', ]


@admin.register(models.MergeQueue)
class MergeQueueAdmin(admin.ModelAdmin):

    model = models.MergeQueue

    readonly_fields = ['id', ]
    list_display = ['id', 'num_entries',]

    show_full_result_count = False

    inlines = [
        MergeQueueEntryInline,
    ]

    def num_entries(self, obj):
        return obj.entries.count()
