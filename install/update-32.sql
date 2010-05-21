CREATE TABLE `advertisements` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `podcast_id` integer NOT NULL,
    `title` varchar(100) NOT NULL,
    `text` longtext NOT NULL,
    `start` datetime NOT NULL,
    `end` datetime NOT NULL
)
;
ALTER TABLE `advertisements` ADD CONSTRAINT `podcast_id_refs_id_534966` FOREIGN KEY (`podcast_id`) REFERENCES `podcast` (`id`);

