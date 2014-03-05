function (doc)
{
    function searchPodcast(podcast, podcast_id)
    {
        if(podcast.oldid)
        {
            emit([podcast.oldid, podcast_id], null);
        }

        for(var n in podcast.merged_oldids)
        {
            emit([podcast.merged_oldids[n], podcast_id], null);
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
