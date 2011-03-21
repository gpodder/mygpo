function(doc)
{
    if(doc.doc_type == "PodcastUserState")
    {
        affected_devices = [];

        for(n in doc.actions)
        {
            action = doc.actions[n];
            if (affected_devices.indexOf(action.device) == -1)
            {
                affected_devices.push(action.device);
            }
        }

        for(n in affected_devices)
        {
            device = affected_devices[n];

            /*if(doc.disabled_devices && (doc.disabled_devices.indexOf(device) > -1))
            {
                continue;
            }*/

            emit([device, doc.podcast], null);
        }
    }
}

