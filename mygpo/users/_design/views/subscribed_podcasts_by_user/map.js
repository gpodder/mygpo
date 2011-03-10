function(doc)
{
    if(doc.doc_type == "PodcastUserState")
    {
        subscribed_devices = []
        for(n in doc.actions)
        {
            action = doc.actions[n];

            if(action.action == "subscribe")
            {
                subscribed_devices.push(action.device);
            }
            else
            {
                index = subscribed_devices.indexOf(action.device);
                subscribed_devices.splice(index, 1);
            }
        }

        for(n in subscribed_devices)
        {
            device = subscribed_devices[n];
            emit([doc.user_oldid, doc.podcast, device], null);
        }
    }
}
