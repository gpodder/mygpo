
-- Bug 656 --
ALTER TABLE podcast ADD COLUMN logo_url VARCHAR(1000);

-- Bug 649 --
CREATE TABLE `sync_group` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL
);

ALTER TABLE user DROP COLUMN default_device_id;
ALTER TABLE device ADD COLUMN sync_group_id INT REFERENCES sync_group(id);
ALTER TABLE device ADD COLUMN `uid` varchar(50) NOT NULL;
