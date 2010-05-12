alter table podcast_tags modify tag varchar(100) character set utf8 collate utf8_general_ci not null;

DROP VIEW IF EXISTS episode_toplist;

CREATE VIEW episode_toplist AS
    SELECT episode_id AS id, episode_id, count(episode_id) AS listeners
    FROM recent_unique_plays
    GROUP BY episode_id
    HAVING listeners > 0
    ORDER BY listeners;


