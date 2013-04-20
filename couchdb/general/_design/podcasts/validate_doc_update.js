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

    function check(cond, message)
    {
        message = message || "Condition check failed";
        if(!cond)
        {
            throw({forbidden: message});
        }
    }

    function checkPodcast(podcast)
    {
        last_timestamp = null;
        if(podcast.subscribers)
        {
            for(var i=0, len=podcast.subscribers.length; sub=podcast.subscribers[i], i<len; i++)
            {
                check((last_timestamp == null) || (last_timestamp < sub.timestamp), "Subscriber Data must be sorted");
                last_timestamp = sub.timestamp;
            }
        }
    }

    if(newDoc.doc_type == "PodcastGroup")
    {
        for(var n=0, len=newDoc.podcasts.length; podcast=newDoc.podcasts[n], n<len; n++)
        {
            if(oldDoc)
            {
                oldpodcast = oldDoc.podcasts[n];
            }
            else
            {
                oldpodcast = null;
            }

            require(podcast, "id");
            require(podcast, "group");
            check(podcast.group == newDoc._id);
            checkPodcast(podcast);
        }
    }
    else if(newDoc.doc_type == "Podcast")
    {
        checkPodcast(newDoc);
    }
}
