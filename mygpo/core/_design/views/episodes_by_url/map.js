function(doc)
{
    function searchPodcast(podcast)
    {
        for(e_id in podcast.episodes)
        {
            episode = podcast.episodes[e_id];
            for(var n=0, length=episode.urls.length; url=episode.urls[n], n<length; n++)
            {
                emit(url, episode);
            }
        }
    }


    if(doc.doc_type == 'Podcast')
    {
        searchPodcast(doc);
    }
    else if (doc.doc_type == 'PodcastGroup')
    {
        for(var n=0; n<doc.podcasts.length; n++)
        {
            podcast = doc.podcasts[n];
            searchPodcast(podcast);
        }
    }
}
