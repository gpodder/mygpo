function (doc)
{
    function getLanguage(podcast)
    {
        if (podcast.language)
        {
            return podcast.language.slice(0, 2);
        }

        return null;
    };

    function doEmit(language, subscribers)
    {
        if(subscribers <= 0)
        {
            return;
        }

        emit(["", subscribers], null);

        if(language)
        {
            emit([language, subscribers], null);
        }
    }

    if (doc.doc_type == "Podcast")
    {
        var language = getLanguage(doc);

        if(doc.subscribers.length)
        {
            subscribers = doc.subscribers[doc.subscribers.length-1].subscriber_count;
        }
        else
        {
            subscribers = 0;
        }

        doEmit(language, subscribers);
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        var subscribers = 0;
        var language = null;

        for(var n in doc.podcasts)
        {
            var podcast = doc.podcasts[n];
            if (podcast.subscribers.length)
            {
                subscribers += podcast.subscribers[podcast.subscribers.length-1].subscriber_count;
            }

            if(!language)
            {
                language = getLanguage(podcast);
            }
        }

        doEmit(language, subscribers);
    }
}
