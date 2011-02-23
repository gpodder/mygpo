function(doc)
{
    function searchPodcast(podcast)
    {
        var d = new Document();
        d.add(podcast.title);

        for(n in podcast.urls)
        {
            d.add(podcast.urls[n]);
        }
        d.add(podcast.description);
        return d;
    }

    if(doc.doc_type == "Podcast")
    {
        return searchPodcast(doc);
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        podcast = doc.podcasts[0];
        return searchPodcast(podcast);
    }
}
