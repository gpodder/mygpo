function(newDoc, oldDoc, userCtx)
{
    function require(doc, field, message)
    {
        message = message || "Document must have a " + field;
        if (doc[field] == void 0 || doc[field] == null || doc[field].length == 0)
        {
            throw({forbidden: message});
        }
    }

    if(newDoc.doc_type == "PodcastUserState")
    {
        require(newDoc, "podcast");

        subscribed_devices = [];
        last_timestamp = null;

        for(n in newDoc.actions)
        {
            action = newDoc.actions[n];


            if((last_timestamp != null) && (action.timestamp < last_timestamp))
            {
                throw({forbidden: "The actions in PodcastUserState " + newDoc._id + " must be in order"});
            }
            last_timestamp = action.timestamp;


            index = subscribed_devices.indexOf(action.device);
            if(action.action == "subscribe")
            {
                if(index > -1)
                {
                    throw({forbidden: "Can not subscribe twice on device " + action.device + " in podcast state " + newDoc._id});
                }

                subscribed_devices.push(action.device);
            }
            else
            {
                if(index == -1)
                {
                    throw({forbidden: "Can not unsubscribe on device " + action.device + " on which the podcast is not subscribed in podcast state " + newDoc._id});
                }

                subscribed_devices.splice(index, 1);
            }

        }
    }
}
