
DROP TRIGGER IF EXISTS subscription_log_trigger;

DELIMITER //
CREATE TRIGGER subscription_log_trigger BEFORE INSERT ON subscription_log
FOR EACH ROW
BEGIN
	declare help_id INT;
	set help_id = 0;

	SELECT count(a.user_id) into help_id FROM current_subscription a 
			where a.device_id = new.device_id
			and a.podcast_id = new.podcast_id;

	IF new.action = 1 THEN
		
		IF help_id > 0 THEN
			call Fail('This subscription already exists!');
		END IF;
    	ELSE
    		IF help_id < 1 THEN
			call Fail('This subscription not exists!');
		END IF;
    	END IF;

END;//
DELIMITER ;

DROP TRIGGER IF EXISTS podcast_trig_url_unique;

DELIMITER //
CREATE TRIGGER podcast_trig_url_unique BEFORE INSERT ON podcast
FOR EACH ROW
BEGIN
	declare help_url varchar(3000);
	set help_url = 0;
  
   	SELECT count(a.url) into help_url FROM podcast a where a.url=new.url;

	IF help_url > 0 THEN
		call Fail('This URL already exists!');
	END IF;

END;//
DELIMITER ;

ALTER TABLE user ADD COLUMN id INT PRIMARY KEY AUTO_INCREMENT;

DROP VIEW IF EXISTS public_subscription;
CREATE VIEW public_subscription AS
    SELECT cs.podcast_id,
           cs.user_id,
           ifnull(s.public, true) AS pub_subscription,
           ifnull(u.public_profile,true) AS pub_profile
    FROM (current_subscription cs
       LEFT JOIN subscription s
       ON cs.podcast_id = s.podcast_id
       AND cs.user_id = s.user_id)
          LEFT JOIN user u
          ON s.user_id = u.user_ptr_id
       HAVING pub_subscription=1
       AND pub_profile;

DELIMITER $$
DROP PROCEDURE IF EXISTS update_toplist $$
CREATE PROCEDURE update_toplist()
BEGIN
	DECLARE deadlock INT DEFAULT 0;
    	DECLARE attempts INT DEFAULT 0;

	try_loop:WHILE (attempts<3) DO
	BEGIN
		DECLARE deadlock_detected CONDITION FOR 1213;
    		DECLARE EXIT HANDLER FOR deadlock_detected
    			BEGIN
    				ROLLBACK;
    				SET deadlock=1;
    			END;
    		SET deadlock=0;
   			
    		START TRANSACTION;
			DELETE FROM toplist;
			INSERT INTO toplist (SELECT a.podcast_id, COUNT(*) AS count_subscription
						FROM (SELECT DISTINCT podcast_id, user_id 
							FROM public_subscription) a 
						GROUP BY podcast_id);
			
			COMMIT;
		END;
		IF deadlock=0 THEN
    			LEAVE try_loop;
    		ELSE
    			SET attempts=attempts+1;
    		END IF;
    	END WHILE try_loop;

	IF deadlock=1 THEN
		call FAIL('Toplist is not updated!');
	END IF;

END $$
DELIMITER ;

DROP VIEW IF EXISTS current_subscription;

CREATE VIEW current_subscription AS SELECT device_id, podcast_id, c.user_ptr_id AS user_id, a.timestamp as subscribed_since, sum(a.action) as summe 
    FROM (subscription_log a JOIN device b on a.device_id=b.id) 
        JOIN user c on b.user_id=c.user_ptr_id 
    GROUP BY a.podcast_id, b.user_id 
    having summe>0;


-- podcast
create index url_index on podcast ( url (50) );
create index title_index on podcast ( title (50) );
create index last_update_index on podcast (last_update);

-- user
create index user_ptr_index on user (user_ptr_id);
create index public_profile_index on user (public_profile);

-- device
create index name_index on device (name);
create index user_index on device (user_id);
create index type_index on device (type);
create index uid_index on device (uid);
create index sync_g_index on device (sync_group_id);

-- subscription_log
create index podcast_index on subscription_log(podcast_id);
create index action_index on subscription_log(action);
create index timestamp_index on subscription_log(timestamp);
create index device_index on subscription_log(device_id);


