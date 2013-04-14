function(doc)
{
    if(doc.doc_type == "EpisodeUserState")
    {
        for(var n in doc.actions)
        {
            var action = doc.actions[n];

            var action_obj = {
                    podcast:   doc.podcast_ref_url,
                    episode:   doc.ref_url,
                    action:    action.action,
                    timestamp: action.timestamp.slice(0, action.timestamp.length-1),
                }

            if(action.device != null)
            {
                action_obj["device_id"] = action.device;
            }
            if(action.started != null)
            {
                action_obj["started"] = action.started;
            }
            if(action.playmark != null)
            {
                action_obj["position"] = action.playmark;
            }
            if(action.total != null)
            {
                action_obj["total"] = action.total;
            }

            emit([
                    doc.user,
                    doc.podcast,
                    action.device,
                    action.upload_timestamp,
                ], action_obj
            );
        }
    }
}
