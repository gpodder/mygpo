function(doc)
{
    if(doc.doc_type == 'Podcast')
    {
        for(e_id in doc.episodes)
        {
            episode = doc.episodes[e_id];
            for(var n=0, length=episode.urls.length; url=episode.urls[n], n<length; n++)
            {
                emit(url, episode);
            }
        }
    }
}
