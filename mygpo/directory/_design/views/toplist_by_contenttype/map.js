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
        if (doc.subscribers.length)
        {
            for(n=0, len=doc.content_types.length; val=doc.content_types[n], n<len; n++)
            {
                emit([  val,
                        doc.subscribers[doc.subscribers.length-1].subscriber_count
                     ], null);
            }
        }
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        var sum = 0;
        var types = [];
        for(var i=0, len=doc.podcasts.length; p=doc.podcasts[i], i<len; i++)
        {
            if (p.subscribers.length)
            {
                sum += p.subscribers[p.subscribers.length-1].subscriber_count;
            }
            types.push(p.content_types);
        }

        types = unique(types);

        if (sum > 0)
        {
            for(var n=0, c_len=types.length; c=types[n], n<c_len; n++)
            {
                emit([c, sum], null);
            }
        }
    }
}
