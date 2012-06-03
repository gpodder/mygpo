function(doc)
{
    if(doc.doc_type == "EpisodeUserState")
    {
        if(doc.actions.length < 1)
        {
            return;
        }

        action = doc.actions[doc.actions.length-1];

        action_obj = {
                podcast_url:   doc.podcast_ref_url,
                episode_url:   doc.ref_url,
                podcast_id:    doc.podcast,
                episode_id:    doc.episode,
                action:        action.action,
                timestamp:     action.timestamp.slice(0, action.timestamp.length-1),
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


        emit([doc.user, doc.podcast, doc.episode], action_obj);
    }
}
