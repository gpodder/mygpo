function(doc)
{
    if(doc.doc_type == "Episode")
    {
        if(doc.slug != null)
        {
            emit([doc.podcast, doc.slug], null);
        }

        if(doc.merged_slugs)
        {
            for(n in doc.merged_slugs)
            {
                emit([doc.podcast, doc.merged_slugs[n]], null);
            }
        }
    }
}
