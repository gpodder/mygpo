function(doc)
{
    if (doc.doc_type == 'Podcast')
    {
        if(doc.license)
        {
            emit(doc.license, null);
        }
    }
    else if(doc.doc_type == 'PodcastGroup')
    {
        for(var n in doc.podcasts)
        {
            var podcast = doc.podcasts[n];
            if (podcast.license)
            {
                emit(podcast.license, null);
                return;
            }
        }
    }
}
