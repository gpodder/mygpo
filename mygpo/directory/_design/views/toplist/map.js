function (doc)
{
    function unique(arr) {
        var a = [];
        var l = arr.length;
        for(var i=0; i<l; i++) {
            for(var j=i+1; j<l; j++) {
                if (arr[i] === arr[j])
                    j = ++i;
            }
            a.push(arr[i]);
        }
        return a;
    };

    function searchObject(obj, languages, types)
    {
        if (obj.language)
        {
            languages.push(obj.language.slice(0, 2));
        }

        if (obj.content_types)
        {
            for(n in obj.content_types)
            {
                types.push(obj.content_types[n]);
            }
        }
    };

    function doEmit(toplist_type, types, languages, value)
    {
        if(value > 0)
        {
            emit([toplist_type, "none", value], null);

            for(n in types)
            {
                emit([toplist_type, "type", types[n], value], null);

                for(m in languages)
                {
                    emit([toplist_type, "type-language", types[n], languages[m], value], null);
                }
            }

            for(m in languages)
            {
                emit([toplist_type, "language", languages[m], value], null);
            }
        }
    }

    if (doc.doc_type == "Podcast")
    {
        types = [];
        languages = []
        searchObject(doc, languages, types);

        if(doc.subscribers.length)
        {
            subscribers = doc.subscribers[doc.subscribers.length-1].subscriber_count;
        }
        else
        {
            subscribers = 0;
        }

        doEmit("Podcast", types, languages, subscribers);
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        var subscribers = 0;
        var types = [];
        var languages = []

        for(n in doc.podcasts)
        {
            podcast = doc.podcasts[n];
            if (podcast.subscribers.length)
            {
                subscribers += podcast.subscribers[podcast.subscribers.length-1].subscriber_count;
            }

            searchObject(podcast, languages, types);
        }

        types = unique(types);
        languages = unique(languages);

        doEmit("Podcast", types, languages, subscribers);
    }
}
