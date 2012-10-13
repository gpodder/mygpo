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

        if (subscribed_devices.length > 0)
        {
            emit([doc.podcast, doc.user], null);
        }
    }
}
