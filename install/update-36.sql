create temporary table episode_log_tmp like episode_log;

insert into episode_log_tmp (select * from episode_log group by user_id, episode_id, device_id, action, timestamp, playmark, started, total);

delete from episode_log;

insert into episode_log (select * from episode_log_tmp);

