function(doc)
{
    if(doc.doc_type == "PodcastUserState")
    {
        emit([doc.podcast, doc.user_oldid], null);
    }
}
