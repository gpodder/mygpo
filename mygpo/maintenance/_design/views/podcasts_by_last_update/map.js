function(doc)
{
    function searchPodcast(podcast, podcast_id)
    {
        emit([podcast.last_update, podcast_id], null);
    }

    if(doc.doc_type == "Podcast")
    {
        searchPodcast(doc, doc._id);
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        for(var n in doc.podcasts)
        {
            podcast = doc.podcasts[n];
            searchPodcast(podcast, podcast.id);
        }
    }
}
