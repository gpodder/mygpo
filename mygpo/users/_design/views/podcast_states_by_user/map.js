function(doc)
{
    if(doc.doc_type == "PodcastUserState")
    {
        emit([doc.user, doc.podcast], null);
    }
}
