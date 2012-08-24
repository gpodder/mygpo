function(doc)
{
    if(doc.doc_type == "EpisodeUserState")
    {
        for(var n=0; n<doc.actions.length; n++)
        {
            var action = doc.actions[n];
            if(action.action == "play" && action.playmark != 0)
            {
                var seconds = action.playmark - action.started;
                if(seconds)
                {
                    var day = action.timestamp.slice(0, 10);
                    emit([doc.user, day], seconds);
                }
            }
        }
    }
}
