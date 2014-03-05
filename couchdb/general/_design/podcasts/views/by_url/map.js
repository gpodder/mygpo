function(doc)
{
    function searchPodcast(podcast)
    {
        for(var n in podcast.urls)
        {
            emit(podcast.urls[n], null);
        }
    }

    if (doc.doc_type == 'Podcast')
    {
        searchPodcast(doc);
    }
    else if(doc.doc_type == 'PodcastGroup')
    {
        for(var n in doc.podcasts)
        {
            podcast = doc.podcasts[n];
            searchPodcast(podcast);
        }
    }
}
