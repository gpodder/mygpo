function(doc)
{
    if(doc.doc_type == "Episode")
    {
        if(doc.listeners > 0 && doc.released != null)
        {
            day = doc.released.slice(0, 10);
            emit([day, doc.listeners], null);
        }
    }
}
