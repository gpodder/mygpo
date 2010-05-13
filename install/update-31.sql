alter table podcast_tags modify tag varchar(100) character set utf8 collate utf8_general_ci not null;

DROP VIEW IF EXISTS episode_toplist;

CREATE VIEW episode_toplist AS
    SELECT episode_id AS id, episode_id, count(episode_id) AS listeners
    FROM recent_unique_plays
    GROUP BY episode_id
    HAVING listeners > 0
    ORDER BY listeners;

CREATE TABLE related_podcasts (
    id INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
    ref_podcast_id INTEGER NOT NULL,
    rel_podcast_id INTEGER NOT NULL,
    priority INTEGER NOT NULL
);

ALTER TABLE related_podcasts ADD CONSTRAINT ref_podcast_id FOREIGN KEY (ref_podcast_id) REFERENCES podcast (id);
ALTER TABLE related_podcasts ADD CONSTRAINT rel_podcast_id FOREIGN KEY (rel_podcast_id) REFERENCES podcast (id);

