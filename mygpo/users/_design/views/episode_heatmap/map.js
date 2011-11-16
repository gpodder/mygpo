function(doc)
{
    function sortByStarted(a, b)
    {
        x = a.started;
        y = b.started;
        return ((x < y) ? -1 : ((x > y) ? 1 : 0));
    }

    function hasTimeValues(action)
    {
        return ((action != null) && (action.started != null) && (action.playmark != null));
    }

    if(doc.doc_type == "EpisodeUserState")
    {
        if(doc.actions == null || doc.actions.length == 0)
        {
            return;
        }

        actions = doc.actions.slice(0); // creates a copy
        actions = actions.filter(hasTimeValues);
        actions.sort(sortByStarted);

        played_parts = [];
        flat_date = null;

        for(var n in actions)
        {
            action = actions[n];

            if(flat_date == null)
            {
                flat_date = {start: action.started, end: action.playmark};
                played_parts.push(flat_date);
                continue;
            }

            if(action.started <= flat_date.end && action.playmark >= flat_date.end)
            {
                flat_date.end = action.playmark;
            }
            else if(action.started >= flat_date.start && action.playmark <= flat_date.end)
            {
                // part already contained
                continue;
            }
            else
            {
                flat_date = {start: action.started, end: action.playmark};
                played_parts.push(flat_date);
            }
        }

        if (played_parts.length == 0)
        {
            return;
        }

        sections = [];
        for(var n in played_parts)
        {
            part = played_parts[n];
            sections.push(part.start);
            sections.push(part.end);
        }

        emit([doc.podcast, doc.episode, doc.user], sections);
    }
}
