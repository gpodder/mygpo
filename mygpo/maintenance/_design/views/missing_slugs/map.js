function(doc)
{
    function searchPodcast(podcast, podcast_id)
    {
        if(podcast.slug != null)
        {
            return;
        }

        var subscribers;

        if(podcast.subscribers == null || podcast.subscribers.length == 0)
        {
            subscribers = 0;
        }
        else
        {
            subscribers = podcast.subscribers[podcast.subscribers.length-1].subscriber_count;
        }

        emit(["Podcast", subscribers, podcast_id], null);
    };

    function searchEpisode(episode)
    {
        if(episode.slug != null)
        {
            return;
        }

        emit(["Episode", episode.podcast, episode.listeners], null);
    };

    if(doc.doc_type == "Podcast")
    {
        searchPodcast(doc, doc._id);
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        for(n in doc.podcasts)
        {
            searchPodcast(doc.podcasts[n], doc.podcasts[n].id);
        }

    }
    else if(doc.doc_type == "Episode")
    {
        searchEpisode(doc);
    }
}
