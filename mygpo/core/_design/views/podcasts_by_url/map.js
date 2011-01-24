function(doc)
{
    function searchPodcast(podcast)
    {
        for(url in podcast.urls)
        {
            emit(url, podcast);
        }
    }

    if (doc.doc_type == 'Podcast')
    {
        searchPodcast(doc);
    }
    else if(doc.doc_type == 'PodcastGroup')
    {
        for(podcast in doc.podcasts)
        {
            searchPodcast(podcast);
        }
    }
}
