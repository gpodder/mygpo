function(doc)
{
    if(doc.doc_type == "PodcastList")
    {
        emit([doc.user, doc.slug], null);
    }
}
