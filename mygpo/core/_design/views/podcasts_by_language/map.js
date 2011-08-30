function(doc)
{
    function searchPodcast(podcast)
    {
        if(podcast.language)
        {
            emit(podcast.language, null);
        }
    }

    if(doc.doc_type == "Podcast")
    {
        searchPodcast(doc);
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        for(var n in doc.podcasts)
        {
            searchPodcast(doc.podcasts[n]);
        }
    }
}
