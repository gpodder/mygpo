function(doc)
{
    if(doc.doc_type == "PodcastUserState")
    {
        var subscribed_devices = [];

        for(var n in doc.actions)
        {
            var action = doc.actions[n];

            if(action.action == "subscribe")
            {
                subscribed_devices.push(action.device);
            }
            else
            {
                var index = subscribed_devices.indexOf(action.device);
                subscribed_devices.splice(index, 1);
            }
        }

        for(var n in subscribed_devices)
        {
            var device = subscribed_devices[n];

            if(doc.disabled_devices && (doc.disabled_devices.indexOf(device) > -1))
            {
                continue;
            }

            emit([device, doc.podcast], null);
        }
    }
}
