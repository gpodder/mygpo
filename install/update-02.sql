
-- Bug 649 --
DROP TABLE IF EXISTS `sync_group`;
CREATE TABLE `sync_group` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL
);

ALTER TABLE device ADD COLUMN sync_group_id INT REFERENCES sync_group(id);
ALTER TABLE device ADD COLUMN `uid` varchar(50) NOT NULL;

-- selects the latest action for each pair (device_id, podcast_id) --
DROP VIEW IF EXISTS sync_group_subscription_log;
CREATE VIEW sync_group_subscription_log AS
    SELECT subscription_log.id AS id, device_id, podcast_id, action, timestamp, sync_group_id
    FROM subscription_log JOIN device ON device_id = device.id 
    WHERE timestamp IN (
        SELECT max(timestamp) 
        FROM subscription_log 
        GROUP BY podcast_id, device_id
    );

DROP VIEW IF EXISTS sync_group_current_subscription;
CREATE VIEW sync_group_current_subscription AS
    SELECT device_id, podcast_id, c.user_ptr_id AS user_id, a.timestamp as subscribed_since, sync_group_id
    FROM (subscription_log a JOIN device b on a.device_id=b.id) JOIN user c on b.user_id=c.user_ptr_id
    WHERE action='subscribe'
        AND NOT EXISTS (
            SELECT id FROM subscription_log
            WHERE action='unsubscribe'
                AND device_id=a.device_id
                AND podcast_id=a.podcast_id
                AND timestamp > a.timestamp
        );

