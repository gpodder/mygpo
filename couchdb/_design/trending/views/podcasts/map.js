function(doc)
{
    function getLanguage(podcast)
    {
        if (podcast.language)
        {
            return podcast.language.slice(0, 2);
        }

        return null;
    };

    function doEmit(language, prev, cur)
    {
        if(prev == 0)
        {
            return;
        }

        var change = cur / prev;

        /* we only emit improvements */
        if(change <= 1)
        {
            return;
        }

        emit(["", change], null);

        if(language)
        {
            emit([language, change], null);
        }
    }


    if(doc.doc_type == "Podcast")
    {
        var len = doc.subscribers.length;
        if(len < 1)
        {
            return;
        }

        if (len < 2)
        {
            var prev = 1;
        }
        else
        {
            var prev = doc.subscribers[len-2].subscriber_count;
        }

        var cur = doc.subscribers[len-1].subscriber_count;

        var language = getLanguage(doc);

        doEmit(language, prev, cur);
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        var prev = 0;
        var cur = 0;
        var language = null;

        for(var n in doc.podcasts)
        {
            var podcast = doc.podcasts[n];
            var len = podcast.subscribers.length;

            if (len >= 1)
            {
                cur += podcast.subscribers[len-1].subscriber_count;
            }

            if (len >= 2)
            {
                prev += podcast.subscribers[len-2].subscriber_count;
            }

            if(!language)
            {
                language = getLanguage(podcast);
            }
        }

        doEmit(language, prev, cur);

    }
}
