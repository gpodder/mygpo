function(doc)
{
    function searchPodcast(podcast)
    {
        for(e_id in podcast.episodes)
        {
            episode = podcast.episodes[e_id];
            emit(e_id, episode);
        }
    }

    if(doc.doc_type == 'Podcast')
    {
        searchPodcast(doc);
    }
    else if(doc.doc_type == 'PodcastGroup')
    {
        for(var n=0; n<doc.podcasts.length; n++)
        {
            podcast = doc.podcasts[n];
            searchPodcast(podcast);
        }
    }
}
