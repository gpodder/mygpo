ALTER TABLE podcast ADD COLUMN `author` varchar(100);
ALTER TABLE podcast ADD COLUMN `language` varchar(10);

ALTER TABLE episode ADD COLUMN `author` varchar(100);
ALTER TABLE episode ADD COLUMN `duration` integer UNSIGNED;
ALTER TABLE episode ADD COLUMN `filesize` integer UNSIGNED;


DROP VIEW IF EXISTS current_subscription;

CREATE VIEW current_subscription AS SELECT device_id, podcast_id, c.user_ptr_id AS user_id, a.timestamp as subscribed_since, sum(a.action) as summe
    FROM (subscription_log a JOIN device b on a.device_id=b.id)
        JOIN user c on b.user_id=c.user_ptr_id
    WHERE b.deleted = 0
    GROUP BY a.podcast_id, device_id
    having summe>0;


DELIMITER $$
DROP PROCEDURE IF EXISTS delete_inactive_users $$
CREATE PROCEDURE delete_inactive_users()
BEGIN
    DECLARE deadlock INT DEFAULT 0;
    DECLARE attempts INT DEFAULT 0;
    DECLARE done INT DEFAULT 0;
    DECLARE user_help INT DEFAULT 0;
    DECLARE day_count INT DEFAULT 0;
    DECLARE cur1 CURSOR FOR select user_id from registration_registrationprofile where activation_key<>"ALREADY_ACTIVATED";
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

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
OPEN cur1;

            REPEAT
                FETCH cur1 INTO user_help;

                IF NOT done THEN

                    SELECT datediff(date(now()), date(date_joined)) into day_count FROM auth_user where id=user_help;

                    IF day_count > 7 THEN
                        delete from auth_user where id=user_help;
                        delete from registration_registrationprofile where user_id=user_help;
                    END IF;
                END IF;
            UNTIL done END REPEAT;

            CLOSE cur1;

            COMMIT;
        END;
        IF deadlock=0 THEN
                LEAVE try_loop;
            ELSE
                SET attempts=attempts+1;
            END IF;
            END WHILE try_loop;

        IF deadlock=1 THEN
            call FAIL('Inactive users are not deleted!');
        END IF;

END $$
DELIMITER ;

