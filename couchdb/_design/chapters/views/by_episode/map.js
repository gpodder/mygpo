function(doc)
{
    if(doc.doc_type == "EpisodeUserState")
    {
        for(var n in doc.chapters)
        {
            var chapter = doc.chapters[n];
            emit([doc.episode, doc.user], chapter);
        }
    }
}
