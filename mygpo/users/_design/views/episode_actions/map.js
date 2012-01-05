function(doc)
{
    if(doc.doc_type == "EpisodeUserState")
    {
        for(var n in doc.actions)
        {
            var action = doc.actions[n];

            emit([
                    doc.user,
                    action.timestamp,
                    doc.podcast,
                    doc.device,
                ], n
            );
        }
    }
}
