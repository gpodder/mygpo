function(doc)
{
    if(doc.doc_type == "EpisodeUserState")
    {
        emit([doc.user_oldid, doc.episode], null);
    }
}
