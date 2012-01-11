function(doc)
{
    if ((doc.doc_type == "EpisodeUserState") || (doc.doc_type == "PodcastUserState"))
    {
        for(var n in doc.actions)
        {
            var action = doc.actions[n];
            var timestamp = action.timestamp.slice(0, action.timestamp.length-1);

            emit([doc.user, timestamp], n);
        }
    }
}
