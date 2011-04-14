function(doc)
{
    if(doc.doc_type == "Episode")
    {
        if(doc.slug != null)
        {
            emit([doc.podcast, doc.slug], null);
        }
    }
}
