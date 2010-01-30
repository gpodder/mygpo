ALTER TABLE podcast ADD COLUMN `author` varchar(100);

ALTER TABLE episode ADD COLUMN `author` varchar(100);
ALTER TABLE episode ADD COLUMN `duration` integer UNSIGNED;
ALTER TABLE episode ADD COLUMN `filesize` integer UNSIGNED;
