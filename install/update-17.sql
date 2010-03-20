BEGIN;
CREATE TABLE `historic_podcast_data` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `podcast_id` integer NOT NULL,
    `date` date NOT NULL,
    `subscriber_count` integer NOT NULL
)
;
ALTER TABLE `historic_podcast_data` ADD CONSTRAINT `podcast_id_refs_id_aeb8d2a` FOREIGN KEY (`podcast_id`) REFERENCES `podcast` (`id`);
CREATE TABLE `historic_episode_data` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `episode_id` integer NOT NULL,
    `date` date NOT NULL,
    `listener_count` integer NOT NULL
)
;
ALTER TABLE `historic_episode_data` ADD CONSTRAINT `episode_id_refs_id_2f31345e` FOREIGN KEY (`episode_id`) REFERENCES `episode` (`id`);
COMMIT;
