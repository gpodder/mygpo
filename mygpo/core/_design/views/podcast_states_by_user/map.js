function(doc)
{
    if(doc.doc_type == "PodcastUserState")
    {
        emit([doc.user_oldid, doc.podcast], null);
    }
}
