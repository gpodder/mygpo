function(doc)
{
    if(doc.doc_type == "EpisodeUserState")
    {
        if(doc.actions.length < 1)
        {
            return;
        }

        var index = doc.actions.length - 1;
        emit([doc.user, doc.podcast, doc.episode], index);
    }
}
