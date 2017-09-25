default_app_config = 'mygpo.search.apps.SearchConfig'

# Field that should be indexed, with their levels per
# https://docs.djangoproject.com/en/1.11/ref/contrib/postgres/search/#weighting-queries
INDEX_FIELDS = {
    'title': 'A',
    'description': 'B',
}

def get_index_fields(podcast):
    """ Returns a dict of the fields to be included in the search index """
    return {field: getattr(podcast, field) for field in INDEX_FIELDS.keys()}
