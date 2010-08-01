alter table subscription add column settings text not null;
update subscription set settings = '{\"public_subscription\": true}' where public = True;
update subscription set settings = '{\"public_subscription\": false}' where public = False;

alter table user add column settings text not null;
update user set settings = '{\"public_profile\": true}' where public_profile = True;
update user set settings = '{\"public_profile\": false}' where public_profile = False;

alter table device add column settings text not null;

CREATE TABLE `episode_settings` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `episode_id` integer NOT NULL,
    `settings` longtext NOT NULL,
    UNIQUE (`user_id`, `episode_id`)
)
;
ALTER TABLE `episode_settings` ADD CONSTRAINT `episode_id_refs_id_7347523a` FOREIGN KEY (`episode_id`) REFERENCES `episode` (`id`);
ALTER TABLE `episode_settings` ADD CONSTRAINT `user_id_refs_id_23924ff9` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

