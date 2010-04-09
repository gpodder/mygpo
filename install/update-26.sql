
-- it seems episode_toplist need to be re-created if the underlying view changes

DROP VIEW IF EXISTS episode_toplist;

CREATE VIEW episode_toplist AS
    SELECT episode_id AS id, episode_id, count(episode_id) AS listeners
    FROM recent_unique_plays
    GROUP BY episode_id
    ORDER BY listeners;

