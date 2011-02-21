function(doc)
{
    function searchPodcast(podcast)
    {
        for(n in podcast.urls)
        {
            emit(podcast.urls[n], podcast);
        }
    }

    if (doc.doc_type == 'Podcast')
    {
        searchPodcast(doc);
    }
    else if(doc.doc_type == 'PodcastGroup')
    {
        for(n in doc.podcasts)
        {
            podcast = doc.podcasts[n];
            searchPodcast(podcast);
        }
    }
}
