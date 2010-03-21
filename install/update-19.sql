CREATE TABLE `chapters` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `episode_id` integer NOT NULL,
    `device_id` integer,
    `created` datetime NOT NULL,
    `start` integer NOT NULL,
    `end` integer NOT NULL,
    `label` varchar(50) NOT NULL,
    `advertisement` bool NOT NULL
)
;
ALTER TABLE `chapters` ADD CONSTRAINT `episode_id_refs_id_6613a857` FOREIGN KEY (`episode_id`) REFERENCES `episode` (`id`);
ALTER TABLE `chapters` ADD CONSTRAINT `device_id_refs_id_38552f8d` FOREIGN KEY (`device_id`) REFERENCES `device` (`id`);
ALTER TABLE `chapters` ADD CONSTRAINT `user_id_refs_id_2e1e1276` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

