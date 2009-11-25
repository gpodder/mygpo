DROP TABLE IF EXISTS user;
CREATE TABLE user (
    user_ptr_id INT REFERENCES auth_user(id),
    generated_id TINYINT(1) NOT NULL DEFAULT 0,
    public_profile TINYINT(1) NOT NULL DEFAULT 1,
    default_device INT REFERENCES device(id)
);

DROP TABLE IF EXISTS podcast;
CREATE TABLE podcast (
    id INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    url VARCHAR(3000) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
    title VARCHAR(100) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
    description TEXT,
    link VARCHAR(3000) CHARACTER SET utf8 COLLATE utf8_bin,
    last_update TIMESTAMP DEFAULT 0,
    logo_url VARCHAR(1000)
);

DROP TABLE IF EXISTS episode;
CREATE TABLE episode (
    id INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    podcast_id INT REFERENCES podcast (id),
    url VARCHAR(3000) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
    title VARCHAR(100) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
    description TEXT,
    link VARCHAR(3000) CHARACTER SET utf8 COLLATE utf8_bin
);

DROP TABLE IF EXISTS episode_log;
CREATE TABLE episode_log (
    user_id INT REFERENCES user (user_ptr_id),
    episode_id INT REFERENCES episode (id),
    device_id INT REFERENCES device (id),
    action ENUM ('download', 'play', 'sync', 'lock', 'delete') NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    playmark INT DEFAULT 0,
    PRIMARY KEY (user_id, episode_id, action, timestamp, device_id)
);

DROP TABLE IF EXISTS device;
CREATE TABLE device (
    id INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    user_id INT REFERENCES user (user_ptr_id),
    name VARCHAR(100) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
    type ENUM ('desktop', 'laptop', 'mobile', 'server', 'other') NOT NULL
);

DROP TABLE IF EXISTS subscription;
CREATE TABLE subscription (
    user_id INT REFERENCES user (user_ptr_id),
    podcast_id INT REFERENCES podcast (id),
    public TINYINT(1) NOT NULL DEFAULT 1,
    PRIMARY KEY (user_id, podcast_id)
);

DROP TABLE IF EXISTS subscription_log;
CREATE TABLE subscription_log (
    id INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    device_id INT REFERENCES device (id),
    podcast_id INT REFERENCES podcast (id),
    action TINYINT(1) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (device_id, podcast_id, action, timestamp)
);

DROP TABLE IF EXISTS current_subscription;
DROP VIEW IF EXISTS current_subscription;

CREATE VIEW current_subscription AS
	SELECT device_id, podcast_id, c.user_ptr_id AS user_id, a.timestamp as subscribed_since FROM
		(subscription_log a JOIN device b on a.device_id=b.id) JOIN user c on b.user_id=c.user_ptr_id
			WHERE action='subscribe' 
			AND NOT EXISTS (
				SELECT id FROM subscription_log
					WHERE action='unsubscribe'
                    			AND device_id=a.device_id
					AND podcast_id=a.podcast_id
                    			AND timestamp > a.timestamp
				);

DROP TABLE IF EXISTS Error;
CREATE TABLE Error (                                                                                                         
          ErrorGID int(10) unsigned NOT NULL auto_increment,                                                                         
          Message varchar(128) default NULL,                                                                                         
          Created timestamp NOT NULL default CURRENT_TIMESTAMP,                                         
          PRIMARY KEY (ErrorGID),                                                                                                   
          UNIQUE KEY ERROR (Message));
          
DELIMITER $$
DROP PROCEDURE IF EXISTS Fail $$
CREATE PROCEDURE Fail(_Message VARCHAR(128))
BEGIN
  INSERT INTO Error (Message) VALUES (_Message);
  INSERT INTO Error (Message) VALUES (_Message);
END;$$
DELIMITER ;

DELIMITER //
CREATE TRIGGER podcast_trig_url_unique BEFORE INSERT ON podcast
FOR EACH ROW
BEGIN
	declare help_url varchar(3000);
	set help_url = null;
  
   	SELECT a.url into help_url FROM podcast a where a.url=new.url;

	IF help_url is not null THEN
		call Fail('This URL already exists!');
	END IF;

END;//
DELIMITER ;

DROP TABLE IF EXISTS toplist;
CREATE TABLE toplist (
    	podcast_id INT PRIMARY KEY REFERENCES podcast (id),
    	subscription_count INT NOT NULL DEFAULT 0,
        INDEX(podcast_id)
);

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
			INSERT INTO toplist (SELECT a.podcast_id, count(a.podcast_id) as count_subscription 
				FROM current_subscription a, user b 
				WHERE b.user_ptr_id = a.user_id
				AND b.public_profile = 1
				AND NOT EXISTS (SELECT * FROM subscription 
							WHERE a.podcast_id=podcast_id
							AND a.user_id=user_id
							AND public = 0)
				AND a.device_id = (SELECT min(device_id) FROM current_subscription 
								WHERE a.podcast_id=podcast_id
								AND a.user_id=user_id)
				group by a.podcast_id order by count_subscription DESC);
			
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

DELIMITER //
CREATE TRIGGER subscription_log_trigger BEFORE INSERT ON subscription_log
FOR EACH ROW
BEGIN
	declare help_id INT;
	set help_id = null;

   	SELECT a.user_id into help_id FROM current_subscription a 
			where a.device_id = new.device_id
			and a.podcast_id = new.podcast_id;

	IF new.action = 'subscribe' THEN
    		IF help_id is not null THEN
			call Fail('This subscription already exists!');
		END IF;
    	ELSE
    		IF help_id is null THEN
			call Fail('This subscription not exists!');
		END IF;
    	END IF;

END;//
DELIMITER ;



