--DROP TABLE current_subscription;
--DROP VIEW current_subscription;

CREATE VIEW current_subscription AS SELECT device_id, podcast_id, c.user_ptr_id AS user_id, a.timestamp as subscribed_since, sum(a.action) as summe
    FROM (subscription_log a JOIN device b on a.device_id=b.id)
        JOIN user c on b.user_id=c.user_ptr_id
    GROUP BY a.podcast_id, b.user_id
    having summe>0;

