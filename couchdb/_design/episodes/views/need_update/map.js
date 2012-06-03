function(doc)
{
    if(doc.doc_type == "Episode")
    {
        if(!doc.title && (doc.outdated != true))
        {
            emit(doc.podcast, null);
        }
    }
}
