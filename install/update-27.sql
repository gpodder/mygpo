create index podcast_language on podcast(language);
create index episode_language on episode(language);

create index toplist_subsciptions on toplist(subscription_count);
create index timestamp on episode(timestamp);
create index last_update on episode(last_update);
create index outdated on episode(outdated);
create index email on auth_user(email);
create index deleted on device(deleted);

