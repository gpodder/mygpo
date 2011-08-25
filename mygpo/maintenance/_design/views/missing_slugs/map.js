function(doc)
{
    function searchPodcast(podcast, podcast_id)
    {
        var subscribers;

        if(podcast.subscribers == null || podcast.subscribers.length == 0)
        {
            subscribers = 0;
        }
        else
        {
            subscribers = podcast.subscribers[podcast.subscribers.length-1].subscriber_count;
        }

        if((podcast.slug = null) && podcast.title)
        {
            emit(["Podcast", subscribers, podcast_id], null);
        }

        return subscribers;
    }

    function searchEpisode(episode)
    {
        if(episode.slug != null)
        {
            return;
        }
        if(!episode.title)
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
        var subscribers = 0;

        for(var n in doc.podcasts)
        {
            var podcast = doc.podcasts[n];
            subscribers += searchPodcast(podcast, podcast.id);
        }

        if(doc.slug == null)
        {
            emit(["PodcastGroup", subscribers], null);
        }
    }
    else if(doc.doc_type == "Episode")
    {
        searchEpisode(doc);
    }
}
