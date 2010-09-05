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


create temporary table podcast_tags_tmp like podcast_tags;
insert into podcast_tags_tmp (select * from podcast_tags group by tag, podcast_id, source, user_id, weight);
delete from podcast_tags;
insert into podcast_tags (select * from podcast_tags_tmp);


create index podcast_id on directory_entries (podcast_id);
create index podcast_group_id on directory_entries (podcast_group_id);
create index tag on directory_entries (tag);
create index ranking on directory_entries (ranking);

