function(doc, req)
{
    if(doc.doc_type == "PodcastGroup" ||
       doc.doc_type == "Podcast" ||
       doc.doc_type == "Episode")
    {
        return true;
    }

    return false;
}
