function(doc)
{
    if(doc.doc_type == "EpisodeUserState")
    {
        for(var n=doc.actions.length-1; n>=0; n--)
        {
            var action = doc.actions[n];
            if(action.action == "play")
            {
                emit([doc.user, doc.podcast], doc.episode);
                return;
            }
        }
    }
}
