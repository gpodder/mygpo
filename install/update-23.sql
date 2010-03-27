
-- a materialized view storing who listened to which podcast

DROP TABLE IF EXISTS listeners;

CREATE TABLE listeners (
    id INT(11) AUTO_INCREMENT,
    device_id INT(11),
    user_id INT(11),
    episode_id INT(11),
    podcast_id INT(11),
    first_listened DATETIME,
    last_listened DATETIME,

    PRIMARY KEY (id),
    FOREIGN KEY (device_id) REFERENCES device(id),
    FOREIGN KEY (user_id) REFERENCES auth_user(id),
    FOREIGN KEY (episode_id) REFERENCES episode(id),
    FOREIGN KEY (podcast_id) REFERENCES podcast(id),
    UNIQUE (device_id, episode_id)
);


-- initialize with existing data in episode_log

INSERT INTO listeners (device_id, user_id, episode_id, podcast_id, first_listened, last_listened)
    SELECT  device_id,
            user_id,
            episode_id,
            episode.podcast_id as podcast_id,
            min(episode_log.timestamp) AS first_listened,
            max(episode_log.timestamp) AS last_listened
        FROM episode_log JOIN episode ON episode_log.episode_id = episode.id
        WHERE action='play'
        GROUP BY user_id, episode_id, device_id;


-- fills listener materialized view

DROP TRIGGER IF EXISTS episode_log_trigger;

DELIMITER //
CREATE TRIGGER episode_log_trigger BEFORE INSERT ON episode_log
FOR EACH ROW
BEGIN
    DECLARE count INT;
    DECLARE t_podcast_id INT(11);
    set count = 0;
    set t_podcast_id = 0;

    IF new.action = 'play' THEN

        SELECT podcast_id into t_podcast_id from episode where episode.id = new.episode_id;

        SELECT COUNT(*) into count from listeners WHERE
            device_id = new.device_id AND
            user_id = new.user_id AND
            episode_id = new.episode_id;

        IF count > 0 THEN
            UPDATE listeners SET
                last_listened = new.timestamp
                WHERE
                    device_id = new.device_id AND
                    user_id = new.user_id AND
                    episode_id = new.episode_id AND
                    last_listened < new.timestamp;

            UPDATE listeners SET
                first_listened = new.timestamp
                WHERE
                    device_id = new.device_id AND
                    user_id = new.user_id AND
                    episode_id = new.episode_id AND
                    last_listened > new.timestamp;

        ELSE
            INSERT INTO listeners (device_id, user_id, episode_id, podcast_id, first_listened, last_listened)
                VALUES (new.device_id, new.user_id, new.episode_id, t_podcast_id, new.timestamp, new.timestamp);
        END IF;

    END IF;

END;//
DELIMITER ;


-- episode toplist can be based on listener materialized view

DROP VIEW IF EXISTS recent_unique_plays;

CREATE VIEW recent_unique_plays AS
    SELECT DISTINCT user_id, episode_id
    FROM listeners
    WHERE DATEDIFF(NOW(), last_listened) <= 7;


-- it seems episode_toplist need to be re-created if the underlying view changes

DROP VIEW IF EXISTS episode_toplist;

CREATE VIEW episode_toplist AS
    SELECT episode_id AS id, episode_id, count(episode_id) AS listeners
    FROM recent_unique_plays
    GROUP BY episode_id
    ORDER BY listeners
    DESC LIMIT 100;


