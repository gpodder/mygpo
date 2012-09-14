function(doc, req)
{
    if(doc.doc_type != "EpisodeUserState")
    {
        return false;
    }

    if(doc._deleted == true)
    {
        return false;
    }

    if(!doc.actions)
    {
        return false;
    }

    function isPlayEvent(action)
    {
        return action.action == "play";
    }

    return doc.actions.some(isPlayEvent);
}
