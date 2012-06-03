function(doc)
{
    if(doc.doc_type == "PodcastUserState")
    {
        for(n in doc.tags)
        {
            emit([doc.tags[n], doc.podcast], 0.5);
        }
    }
}

