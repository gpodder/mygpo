function(doc, req)
{
    if(doc.doc_type != "EpisodeUserState")
    {
        return false;
    }

    function isPlayEvent(action)
    {
        return action.action == "play";
    }

    return doc.actions.some(isPlayEvent);
}
