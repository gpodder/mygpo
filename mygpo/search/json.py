
""" Converts models to a JSON representation """


def podcast_to_json(podcast):
    """ Convert a podcast to JSON for indexing """
    doc = {
        'title': podcast.title,
        'subtitle': podcast.subtitle,
        'description': podcast.description,
        'link': podcast.link,
        'language': podcast.language,
        'last_update': podcast.last_update,
        'created': podcast.created,
        # modified is not indexed
        'license': podcast.license,  # maybe get a license name here?
        # flattr_url
        'content_types': list(filter(None, podcast.content_types)),
        'outdated': podcast.outdated,
        'author': podcast.author,
        'logo_url': podcast.logo_url,
        # group, group_member_name ???
        'subscribers': podcast.subscribers,
        # restrictions ?
        # common_episode_title
        # new_location
        'latest_episode_timestamp': podcast.latest_episode_timestamp,
        'episode_count': podcast.episode_count,
        # hub
        'twitter': podcast.twitter,
        # update_interval
        'slugs': [s.slug for s in podcast.slugs.all()],
        'urls': [u.url for u in podcast.urls.all()],
    }

    return doc
