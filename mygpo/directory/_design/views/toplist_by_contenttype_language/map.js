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

    if (doc.doc_type == "Podcast")
    {
        if (doc.subscribers.length && doc.language)
        {
            for(n=0, len=doc.content_types.length; val=doc.content_types[n], n<len; n++)
            {
                emit([  val,
                        doc.language.slice(0, 2),
                        doc.subscribers[doc.subscribers.length-1].subscriber_count
                     ], null);
            }
        }
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        var sum = 0;
        var types = [];
        var lang = []
        for(var i=0, len=doc.podcasts.length; p=doc.podcasts[i], i<len; i++)
        {
            if (p.subscribers.length)
            {
                sum += p.subscribers[p.subscribers.length-1].subscriber_count;
            }
            types.push(p.content_types);
            lang.push(p.language.slice(0, 2));
        }

        types = types.unique();
        lang = lang.unique();

        if (sum > 0)
        {
            for(var n=0, c_len=types.length; c=types[n], n<c_len; n++)
            {
                for(var i=0, l_len=lang.length; l=lang[i], i<l_len; i++)
                {
                    emit([c, l, sum], null);
                }
            }
        }
    }
}
