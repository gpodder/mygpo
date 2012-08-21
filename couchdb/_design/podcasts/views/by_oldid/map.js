function (doc)
{
    function searchPodcast(podcast)
    {
        if(podcast.oldid)
        {
            emit(podcast.oldid, null);
        }

        for(var n in podcast.merged_oldids)
        {
            emit(podcast.merged_oldids[n], null);
        }
    }

    if(doc.doc_type == "Podcast")
    {
        searchPodcast(doc);
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        for(var i in doc.podcasts)
        {
            searchPodcast(doc.podcasts[i]);
        }
    }
}
