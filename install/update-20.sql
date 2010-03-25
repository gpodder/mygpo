DROP VIEW IF EXISTS current_subscription;

DROP TABLE IF EXISTS subscriptions;

CREATE TABLE subscriptions (
    id INTEGER(11) AUTO_INCREMENT,
    device_id INTEGER (11),
    podcast_id INTEGER(11),
    user_id INTEGER(11),
    subscribed_since DATETIME,

    PRIMARY KEY (id),
    FOREIGN KEY (device_id) REFERENCES device(id),
    FOREIGN KEY (podcast_id) REFERENCES podcast(id),
    FOREIGN KEY (user_id) REFERENCES auth_user(id)
);

INSERT INTO subscriptions (device_id, podcast_id, user_id, subscribed_since)
    SELECT device_id, podcast_id, c.user_ptr_id AS user_id, a.timestamp AS subscribed_since
        FROM (subscription_log a JOIN device b on a.device_id=b.id)
            JOIN user c on b.user_id=c.user_ptr_id
        WHERE b.deleted = 0
        GROUP BY a.podcast_id, device_id
        having sum(a.action)>0;


DROP VIEW IF EXISTS current_subscription;
CREATE VIEW current_subscription AS SELECT subscriptions.id AS id, device_id, podcast_id, subscriptions.user_id as user_id, subscribed_since
    FROM subscriptions JOIN device on subscriptions.device_id = device.id
    WHERE device.deleted = 0;


DROP TRIGGER IF EXISTS subscription_log_trigger;

DELIMITER //
CREATE TRIGGER subscription_log_trigger BEFORE INSERT ON subscription_log
FOR EACH ROW
BEGIN
    DECLARE count INT;
    DECLARE t_user_id INT(11);
    set count = 0;
    set t_user_id = 0;

    SELECT count(a.user_id) into count FROM current_subscription a
            where a.device_id = new.device_id
            and a.podcast_id = new.podcast_id;

    SELECT user_id into t_user_id FROM device WHERE id = new.device_id;

    IF new.action = 1 THEN

        IF count > 0 THEN
            call Fail('This subscription already exists!');
        ELSE
            INSERT INTO subscriptions (device_id, podcast_id, user_id, subscribed_since) VALUES (new.device_id, new.podcast_id, t_user_id, new.timestamp);
        END IF;
    ELSE
        IF count < 1 THEN
            call Fail('This subscription not exists!');
        ELSE
            DELETE FROM subscriptions WHERE device_id = new.device_id and podcast_id = new.podcast_id;
        END IF;
    END IF;

END;//
DELIMITER ;

