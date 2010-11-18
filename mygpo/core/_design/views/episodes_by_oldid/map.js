function(doc)
{
    if(doc.doc_type == 'Podcast')
    {
        for(e_id in doc.episodes)
        {
            episode = doc.episodes[e_id];
            emit(episode.oldid, episode);
        }
    }
}
