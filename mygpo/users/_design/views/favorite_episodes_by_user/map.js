function(doc)
{
    if(doc.doc_type == 'EpisodeUserState')
    {
        if (doc.settings && doc.settings.is_favorite)
        {
            emit(doc.user, doc.episode);
        }
    }
}
