function(doc)
{
    function searchPodcast(podcast, podcast_id)
    {
        if(podcast.language)
        {
            emit([podcast.language, podcast_id], null);
        }
    }

    if(doc.doc_type == "Podcast")
    {
        searchPodcast(doc, doc._id);
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        for(var n in doc.podcasts)
        {
            var podcast = doc.podcasts[n];
            searchPodcast(podcast, podcast.id);
        }
    }
}
