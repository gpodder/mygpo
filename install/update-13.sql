
-- Bug 785 --
ALTER TABLE device ADD COLUMN deleted tinyint(1) NOT NULL DEFAULT 0;
DROP VIEW IF EXISTS current_subscription;

CREATE VIEW current_subscription AS SELECT device_id, podcast_id, c.user_ptr_id AS user_id, a.timestamp as subscribed_since, sum(a.action) as summe
    FROM (subscription_log a JOIN device b on a.device_id=b.id)
        JOIN user c on b.user_id=c.user_ptr_id
    WHERE b.deleted = 0
    GROUP BY a.podcast_id, device_id
    having summe>0;

