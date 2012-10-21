function (doc)
{
    function searchPodcast(podcast)
    {
        if(!podcast.title || !podcast.title.trim() || !podcast.description || !podcast.description.trim() || !podcast.logo_url)
        {
            return;
        }

        var random_key = 1;

        if(podcast.random_key)
        {
            random_key = podcast.random_key;
        }

        emit(["", random_key], null);

        if(podcast.language)
        {
            emit([podcast.language, random_key], null);
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
