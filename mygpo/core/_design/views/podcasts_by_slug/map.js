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
            for(m in podcast.merged_slugs)
            {
                emit([podcast.merged_slugs[m], podcast_id], null);
            }
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
