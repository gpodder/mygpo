CREATE TABLE `publisher` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `podcast_id` integer NOT NULL
)
;
ALTER TABLE `publisher` ADD CONSTRAINT `podcast_id_refs_id_39ce950d` FOREIGN KEY (`podcast_id`) REFERENCES `podcast` (`id`);
ALTER TABLE `publisher` ADD CONSTRAINT `user_id_refs_id_22692cb3` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

-- fixing bug 904
alter table episode modify timestamp timestamp null;
update episode set timestamp = null where title = '';

