
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

	IF new.action = 'subscribe' THEN
		
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

