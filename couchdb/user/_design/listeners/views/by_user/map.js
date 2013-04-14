function(doc)
{
    if(doc.doc_type == "EpisodeUserState")
    {
        for(var n=doc.actions.length-1; n>=0; n--)
        {
            var action = doc.actions[n];
            if(action.action == "play")
            {
                var day = action.timestamp.slice(0, 10);
                emit([doc.user, day], doc.episode);
                return;
            }
        }
    }
}
