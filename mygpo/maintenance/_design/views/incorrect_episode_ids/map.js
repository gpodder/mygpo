function(doc)
{
    if(doc.doc_type == "EpisodeUserState")
    {
        if(doc.episode == doc.podcast)
        {
            emit(null, null);
        }
    }
}
