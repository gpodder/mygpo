DROP PROCEDURE IF EXISTS update_suggestion;
DROP PROCEDURE IF EXISTS update_suggestion_for;

CREATE TABLE `suggestion_blacklist` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `podcast_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    UNIQUE (`podcast_id`, `user_id`)
);

ALTER TABLE `suggestion_blacklist` ADD CONSTRAINT `podcast_id` FOREIGN KEY (`podcast_id`) REFERENCES `podcast` (`id`);
ALTER TABLE `suggestion_blacklist` ADD CONSTRAINT `user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

