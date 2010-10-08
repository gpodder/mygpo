function(doc)
{
    if(doc.doc_type == "PodcastGroup")
    {
        if(doc.oldid)
        {
            emit(doc.oldid, doc);
        }
    }
}
