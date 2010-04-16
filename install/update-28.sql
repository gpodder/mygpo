CREATE TABLE `podcast_groups` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title` varchar(100) NOT NULL
)
;

alter table podcast add column `group_id` integer default null;
alter table podcast add column `group_member_name` varchar(20) default null;

ALTER TABLE podcast ADD CONSTRAINT `group_id` FOREIGN KEY (`group_id`) REFERENCES `podcast_groups` (`id`);

alter table toplist drop primary key;
alter table toplist add primary key (id);
alter table toplist modify column podcast_id integer null;
alter table toplist add column `podcast_group_id` integer default null;
ALTER TABLE toplist ADD CONSTRAINT `podcast_group_id` FOREIGN KEY (`podcast_group_id`) REFERENCES `podcast_groups` (`id`);

DROP PROCEDURE IF EXISTS update_toplist;

