function(doc)
{
    if(doc.doc_type == "EpisodeUserState")
    {
        emit([doc.user_oldid, doc.podcast_ref_url, doc.ref_url], null);
    }
}
