function(doc)
{
    if (doc.doc_type == "Podcast")
    {
        emit(doc._id, null);
    }
    else if (doc.doc_type == "PodcastGroup")
    {
        emit(doc._id, null);

        for(var n=0; n<doc.podcasts.length; n++)
        {
            var podcast = doc.podcasts[n];
            emit(podcast.id, null);
        }
    }
}
