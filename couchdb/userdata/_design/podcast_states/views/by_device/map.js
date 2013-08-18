function(doc)
{
    if(doc.doc_type == "PodcastUserState")
    {
        var affected_devices = [];

        for(var n in doc.actions)
        {
            var action = doc.actions[n];
            if (affected_devices.indexOf(action.device) == -1)
            {
                affected_devices.push(action.device);
            }
        }

        for(var n in affected_devices)
        {
            var device = affected_devices[n];

            emit([device, doc.podcast], null);
        }
    }
}

