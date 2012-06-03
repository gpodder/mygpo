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
        d.add(podcast.title);

        for(var n in podcast.urls)
        {
            d.add(podcast.urls[n]);
        }
        d.add(podcast.description);

        d.add(num_subscribers, {"field":"subscribers", "type": "int"});

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
