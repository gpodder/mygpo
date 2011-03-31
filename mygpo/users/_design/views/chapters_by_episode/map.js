function(doc)
{
    if(doc.doc_type == "EpisodeUserState")
    {
        for(n in doc.chapters)
        {
            chapter = doc.chapters[n];
            emit([doc.episode, doc.user_oldid], chapter);
        }
    }
}
