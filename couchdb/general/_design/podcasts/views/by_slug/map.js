function (doc)
{
    function searchPodcast(podcast, podcast_id)
    {
        if(podcast.slug)
        {
            emit([podcast.slug, podcast_id], null);
        }

        if(podcast.merged_slugs)
        {
            for(var n in podcast.merged_slugs)
            {
                emit([podcast.merged_slugs[n], podcast_id], null);
            }
        }
    }

    if(doc.doc_type == "Podcast")
    {
        searchPodcast(doc, doc._id);
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        searchPodcast(doc, doc._id);

        for(var n in doc.podcasts)
        {
            var podcast = doc.podcasts[n];
            searchPodcast(podcast, podcast.id);
        }
    }
}
