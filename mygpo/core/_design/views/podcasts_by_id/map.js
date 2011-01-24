function(doc)
{
    if(doc.doc_type == 'Podcast')
    {
        emit(doc._id, doc);
    }
    else if(doc.doc_type == 'PodcastGroup')
    {
        for(p in doc.podcasts)
        {
            emit(p.id, p);
        }
    }
}
