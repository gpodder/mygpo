function (doc)
{
    function searchPodcast(podcast, podcast_id)
    {
        if(podcast.slug)
        {
            emit([podcast.slug, podcast_id], null);
        }
    }

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
}
