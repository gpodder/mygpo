function(doc)
{
    function searchPodcast(podcast, podcast_id)
    {
        for(e_id in podcast.episodes)
        {
            episode = podcast.episodes[e_id];
            episode.podcast = podcast_id;
            emit(e_id, episode);
        }
    }

    if(doc.doc_type == 'Podcast')
    {
        searchPodcast(doc, doc._id);
    }
    else if(doc.doc_type == 'PodcastGroup')
    {
        for(var n=0; n<doc.podcasts.length; n++)
        {
            podcast = doc.podcasts[n];
            searchPodcast(podcast, podcast.id);
        }
    }
}
