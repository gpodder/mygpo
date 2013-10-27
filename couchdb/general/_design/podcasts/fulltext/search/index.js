function(doc)
{
    function getSubscribers(podcast)
    {
        if(podcast.subscribers.length)
        {
            var l = podcast.subscribers.length;
            return podcast.subscribers[l-1].subscriber_count;
        }
        return 0;
    }

    function searchPodcast(podcast, num_subscribers)
    {
        var d = new Document();

        var boost = 0;

        if(num_subscribers > 0)
        {
            /* Boost documents w/ more subscribers up to 1000 ^= .5 boost */
            boost = Math.min(.5, num_subscribers / 2000);
        }

        d.add(podcast.title, {"field": "title", "boost": 1.6+boost});
        d.add(podcast.description, {"field": "description", "boost": 1+boost});
        return d;
    }

    if(doc.doc_type == "Podcast")
    {
        var num_subscribers = getSubscribers(doc);
        return searchPodcast(doc, num_subscribers);
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        var num_subscribers = 0;
        for(var n in doc.podcasts)
        {
            num_subscribers += getSubscribers(doc.podcasts[n]);
        }

        var podcast = doc.podcasts[0];
        return searchPodcast(podcast, num_subscribers);
    }
}
