alter table suggestion add column id int unique auto_increment;

alter table episode add column timestamp timestamp;

CREATE TABLE `ratings` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `target` varchar(15) NOT NULL,
    `user_id` integer NOT NULL,
    `rating` integer NOT NULL,
    `timestamp` datetime NOT NULL
)
;
ALTER TABLE `ratings` ADD CONSTRAINT `user_id_refs_id_6cfe3b5b` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

