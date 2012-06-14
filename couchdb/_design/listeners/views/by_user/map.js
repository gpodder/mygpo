function(doc)
{
    if(doc.doc_type == "EpisodeUserState")
    {
        for(var n=doc.actions.length-1; n>=0; n--)
        {
            var action = doc.actions[n];
            if(action.action == "play")
            {
                emit([doc.user, action.timestamp], {_id: doc.episode});
                return;
            }
        }
    }
}
