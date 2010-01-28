
-- Bug 785 --
ALTER TABLE device ADD COLUMN deleted tinyint(1) NOT NULL DEFAULT 0;

-- remove unique index (user_id, episode_id, timestamp)
alter table episode_log drop index user_id;

