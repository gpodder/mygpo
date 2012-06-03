function(doc)
{
    function searchPodcast(podcast_id, podcast)
    {
        emit(podcast_id, null);

        for(var n in podcast.merged_ids)
        {
            emit(podcast.merged_ids[n], null);
        }
    }

    if(doc.doc_type == "Podcast")
    {
        searchPodcast(doc._id, doc);
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        for(var n in doc.podcasts)
        {
            var podcast = doc.podcasts[n];
            searchPodcast(podcast.id, podcast);
        }
    }
}
