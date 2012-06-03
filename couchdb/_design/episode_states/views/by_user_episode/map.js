function(doc)
{
    if(doc.doc_type == "EpisodeUserState")
    {
        emit([doc.user, doc.episode], null);
    }
}
