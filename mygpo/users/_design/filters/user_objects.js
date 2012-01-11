function(doc, req)
{
    if(doc.doc_type == "EpisodeUserState")
    {
       return true;
    }
    if (doc.doc_type == "PodcastUserState")
    {
       return true;
    }
    if (doc.doc_type == "Suggestions")
    {
        return true;
    }
    return false;
}
