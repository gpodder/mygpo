CREATE TABLE `directory_entries` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `podcast_id` integer,
    `podcast_group_id` integer,
    `tag` varchar(100) NOT NULL,
    `ranking` double precision NOT NULL
)
;
ALTER TABLE `directory_entries` ADD CONSTRAINT `podcast_group_id_refs_id_78579aa5` FOREIGN KEY (`podcast_group_id`) REFERENCES `podcast_groups` (`id`);
ALTER TABLE `directory_entries` ADD CONSTRAINT `podcast_id_refs_id_189112b9` FOREIGN KEY (`podcast_id`) REFERENCES `podcast` (`id`);

