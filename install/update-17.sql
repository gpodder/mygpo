BEGIN;
CREATE TABLE `historic_podcast_data` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `podcast_id` integer NOT NULL,
    `date` date NOT NULL,
    `subscriber_count` integer NOT NULL,
    UNIQUE (`podcast_id`, `date`)
)
;
ALTER TABLE `historic_podcast_data` ADD CONSTRAINT `podcast_id_refs_id_aeb8d2a` FOREIGN KEY (`podcast_id`) REFERENCES `podcast` (`id`);
CREATE TABLE `historic_episode_data` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `episode_id` integer NOT NULL,
    `date` date NOT NULL,
    `listener_count` integer NOT NULL,
    UNIQUE (`episode_id`, `date`)
)
;
ALTER TABLE `historic_episode_data` ADD CONSTRAINT `episode_id_refs_id_2f31345e` FOREIGN KEY (`episode_id`) REFERENCES `episode` (`id`);
COMMIT;


create index podcast_data_index on historic_podcast_data(podcast_id, date);
create index podcast_data_podcast_index on historic_podcast_data(podcast_id);
create index podcast_data_date_index on historic_podcast_data(date);
create index episode_data_index on historic_episode_data(episode_id, date);
create index episode_data_episode_index on historic_episode_data(episode_id);
create index episode_data_date_index on historic_episode_data(date);

