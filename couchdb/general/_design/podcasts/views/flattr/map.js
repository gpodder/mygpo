function(doc)
{
    if (doc.doc_type == 'Podcast')
    {
        if(doc.flattr_url)
        {
            emit(null, null);
        }
    }
    else if(doc.doc_type == 'PodcastGroup')
    {
        for(var n in doc.podcasts)
        {
            var podcast = doc.podcasts[n];
            if (podcast.flattr_url)
            {
                emit(null, null);
                return;
            }
        }
    }
}
