function(doc)
{
    function searchMergedIds(obj)
    {
        if (obj.merged_ids)
        {
            for(var n=0; n<obj.merged_ids.length; n++)
            {
                emit(obj.merged_ids[n], null);
            }
        }
    }

    if (doc.doc_type == "Podcast" || doc.doc_type == "PodcastGroup")
    {
        emit(doc._id, null);
        searchMergedIds(doc);
    }
    if (doc.doc_type == "PodcastGroup")
    {
        for(var n=0; n<doc.podcasts.length; n++)
        {
            var podcast = doc.podcasts[n];
            emit(podcast.id, null);
            searchMergedIds(podcast);
        }
    }
}
