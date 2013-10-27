function(doc)
{
    function checkPodcast(podcast, podcast_id)
    {
        if(podcast.last_update == null)
        {
            return;
        }

        if(podcast.update_interval == null)
        {
            return;
        }

        var date = new Date(podcast.last_update);
        var nextUpdate = new Date(date.getTime() + podcast.update_interval * 1000 * 60 * 60);

        emit(nextUpdate.toISOString(), podcast_id);
    };

    if(doc.doc_type == "Podcast")
    {
        checkPodcast(doc, doc._id);
    }

    if(doc.doc_type == "PodcastGroup")
    {
        for(var n=0; n<doc.podcasts.length; n++)
        {
            var p = doc.podcasts[n];
            checkPodcast(p, p.id);
        }
    }
}
