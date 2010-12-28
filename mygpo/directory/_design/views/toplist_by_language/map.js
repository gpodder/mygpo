function (doc)
{
    function unique(arr) {
        var a = [];
        var l = arr.length;
        for(var i=0; i<l; i++) {
            for(var j=i+1; j<l; j++) {
                // If this[i] is found later in the array
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
            if(doc.language)
            {
                emit([
                        doc.language.slice(0, 2),
                        doc.subscribers[doc.subscribers.length-1].subscriber_count
                     ], null);
            }
        }
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        var sum = 0;
        var lang = [];
        for(i in doc.podcasts)
        {
            var p = doc.podcasts[i];
            if (p.subscribers.length)
            {
                sum += p.subscribers[p.subscribers.length-1].subscriber_count;
            }
            if(p.language)
            {
                lang.push(p.language.slice(0, 2));
            }
        }

        lang = unique(lang);

        if (sum > 0)
        {
            for(var n=0, len=lang.length; val=lang[n], n<len; n++)
            {
                if(val != null)
                {
                    emit([val, sum], null);
                }
            }
        }
    }
}
