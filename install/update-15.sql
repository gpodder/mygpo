DROP VIEW IF EXISTS recent_unique_plays;

CREATE VIEW recent_unique_plays AS
    SELECT DISTINCT user_id, episode_id
    FROM episode_log
    WHERE action='play'
    AND DATEDIFF(NOW(), timestamp) <= 7;


DROP VIEW IF EXISTS episode_toplist;

CREATE VIEW episode_toplist AS
    SELECT episode_id AS id, episode_id, count(episode_id) AS listeners
    FROM recent_unique_plays
    GROUP BY episode_id
    ORDER BY listeners
    DESC LIMIT 100;

CREATE TABLE IF NOT EXISTS `security_tokens` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `token` varchar(32) NOT NULL,
    `object` varchar(64) NOT NULL,
    `action` varchar(10) NOT NULL
);

