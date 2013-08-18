function(doc)
{
    if(doc.doc_type == "PodcastUserState")
    {
        for(n in doc.tags)
        {
            emit([doc.podcast, doc.tags[n]], 0.5);
        }
    }
}
