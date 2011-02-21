function(doc)
{
    if(doc.doc_type == "Podcast")
    {
        emit(doc._id, doc);
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        for(n in doc.podcasts)
        {
            podcast = doc.podcasts[n];
            emit(podcast.id, podcast);
        }
    }
}
