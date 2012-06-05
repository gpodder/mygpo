function(doc)
{
    if(doc.doc_type == "EpisodeUserState")
    {
        emit([doc.user, doc.podcast_ref_url, doc.ref_url], null);
    }
}
