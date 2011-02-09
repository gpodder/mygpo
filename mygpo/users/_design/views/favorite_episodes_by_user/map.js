function(doc)
{
    if(doc.doc_type == 'PodcastUserState')
    {
        for(id in doc.episodes)
        {
            episode = doc.episodes[id];
            if (episode.settings && episode.settings.is_favorite)
            {
                emit(doc.user_oldid, id);
            }
        }
    }
}
