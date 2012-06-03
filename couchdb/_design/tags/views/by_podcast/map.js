function(doc)
{
    function searchPodcast(podcast, podcast_id)
    {
        for(var source in podcast.tags)
        {
            for(var n in podcast.tags[source])
            {
                emit([podcast_id, podcast.tags[source][n]], sourceWeight(source));
            }
        }
    }

    function sourceWeight(source)
    {
        if(source == "feed")
        {
            return 1;
        }
        else if (source == "delicious")
        {
            return 2;
        }
        else
        {
            return 0;
        }
    }

    if(doc.doc_type == "Podcast")
    {
        searchPodcast(doc, doc._id);
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        for(var p in doc.podcasts)
        {
            searchPodcast(p, p.id);
        }
    }
}
