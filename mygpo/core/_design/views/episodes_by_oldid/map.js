function(doc)
{
    function searchPodcast(podcast)
    {
        for(e_id in podcast.episodes)
        {
            episode = podcast.episodes[e_id];
            emit(episode.oldid, episode);
        }
    }

    if(doc.doc_type == 'Podcast')
    {
        searchPodcast(doc)
    }
    else if (doc.doc_type == 'PodcastGroup')
    {
        for(var n=0, length=doc.podcasts.length; n<length, podcast=doc.podcasts[n]; n++)
        {
            searchPodcast(podcast);
        }
    }
}
