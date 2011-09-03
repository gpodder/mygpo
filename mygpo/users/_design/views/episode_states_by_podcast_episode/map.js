function(doc)
{
    if(doc.doc_type == "EpisodeUserState")
    {
        emit([doc.podcast, doc.episode, doc.user_oldid], null);
    }
}
