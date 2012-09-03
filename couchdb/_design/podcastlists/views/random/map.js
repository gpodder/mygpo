function (doc)
{
    if(doc.doc_type == "PodcastList")
    {
        if(!doc.podcasts)
        {
            return;
        }

        var random_key = 1;

        if(doc.random_key)
        {
            random_key = doc.random_key;
        }

        emit(random_key, null);
    }
}
