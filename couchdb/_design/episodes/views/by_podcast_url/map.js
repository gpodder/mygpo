function(doc)
{
    if(doc.doc_type == "Episode")
    {
        for(n in doc.urls)
        {
            url = doc.urls[n];
            emit([doc.podcast, url], null);
        }
    }
}
