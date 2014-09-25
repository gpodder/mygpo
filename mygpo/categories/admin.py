from django.contrib import admin

from mygpo.categories.models import Category, CategoryEntry, CategoryTag


class CategoryEntryInline(admin.TabularInline):
    model = CategoryEntry

    raw_id_fields = ('podcast', )


class CategoryTagInline(admin.TabularInline):
    model = CategoryTag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    model = Category

    list_display = ('title', 'num_podcasts', 'tag_list')

    inlines = [
        CategoryEntryInline,
        CategoryTagInline,
    ]

    def num_podcasts(self, category):
        """ number of entries in a category """
        return category.entries.count()

    def tag_list(self, category):
        return ', '.join(t.tag for t in category.tags.all()[:10])
