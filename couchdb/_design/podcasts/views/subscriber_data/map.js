function(doc)
{
    if(doc.doc_type == "PodcastSubscriberData")
    {
        emit(doc.podcast, null);
    }
}
