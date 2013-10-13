function(doc)
{
    if(doc.doc_type == "Episode")
    {
        if(!doc.outdated)
        {
            emit(doc.podcast, null);
        }
    }
}
