function(doc)
{
    if (doc.doc_type == 'Podcast' || doc.doc_type == 'PodcastGroup')
    {
        emit(doc._id, null);
    }
}
