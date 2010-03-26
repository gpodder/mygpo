-- episode indices
create index episode_podcast_index on episode (podcast_id);
create index episode_url_index on episode (url);

-- episode_log indices
create index user_id on episode_log(user_id);
create index action on episode_log(action);
create index timestamp on episode_log(timestamp);

