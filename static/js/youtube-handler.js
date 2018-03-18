
function embedYoutubeVideo(id, _username, _podcast_url, _episode_url) {

    var params = { allowScriptAccess: "always" };
    var atts = { id: "ytplayer" };

    // store global variables for onytplayerStateChange
    username = _username;
    podcast_url = _podcast_url;
    episode_url = _episode_url;
    already_played = false;

    swfobject.embedSWF("http://www.youtube.com/v/" + id + "?enablejsapi=1&playerapiid=ytplayer",
                       "ytapiplayer", "425", "356", "8", null, null, params, atts);
}


function onYouTubePlayerReady(playerId) {
    player = document.getElementById("ytplayer");
    player.addEventListener("onStateChange", "onytplayerStateChange");
}

function onytplayerStateChange(newState) {

    if ((newState == 1) && !already_played)
    {
        var str = JSON.stringify([{"podcast": podcast_url, "episode": episode_url, "action": "play"}])
        $.post('/api/1/episodes/' + username + '.json', str);
        already_played = true;
    }
}

