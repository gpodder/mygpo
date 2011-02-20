function(doc)
{
    if(doc.doc_type == "Episode")
    {
        for(n in doc.urls)
        {
            emit(doc.urls[n], null);
        }
    }
}
