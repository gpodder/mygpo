function(doc)
{
    function searchPodcast(podcast, podcast_id)
    {
        for(n in podcast.publisher)
        {
            emit(podcast.publisher[n], podcast_id);
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
            podcast = doc.podcasts[n];
            searchPodcast(podcast, podcast.id);
        }
    }
}
