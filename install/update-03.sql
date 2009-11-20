
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

