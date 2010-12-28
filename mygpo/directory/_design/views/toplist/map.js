function (doc)
{
    if (doc.doc_type == "Podcast")
    {
        if (doc.subscribers.length)
        {
            emit(doc.subscribers[doc.subscribers.length-1].subscriber_count, null);
        }
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        sum = 0;
        for(i in doc.podcasts)
        {
            p = doc.podcasts[i];
            if (p.subscribers.length)
            {
                sum += p.subscribers[p.subscribers.length-1].subscriber_count;
            }
        }

        if (sum > 0)
        {
            emit(sum, null);
        }
    }
}
