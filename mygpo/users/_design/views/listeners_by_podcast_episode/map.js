function(doc)
{
    function contains(a, obj)
    {
        for(var i = 0; i < a.length; i++)
        {
            if(a[i] === obj)
            {
                return true;
            }
        }
        return false;
    }

    if(doc.doc_type == "EpisodeUserState")
    {
        for(n=doc.actions.length-1; n>=0; n--)
        {
            action = doc.actions[n];
            if(action.action == "play")
            {
                day = action.timestamp.slice(0, 10);
                emit([doc.podcast, doc.episode, day], doc.user_oldid);
                return;
            }
        }
    }
}
