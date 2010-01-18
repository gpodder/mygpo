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


CREATE TABLE `sanitizing_rules` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `use_podcast` bool NOT NULL,
    `use_episode` bool NOT NULL,
    `search` varchar(100) NOT NULL,
    `replace` varchar(100) NOT NULL,
    `priority` integer UNSIGNED NOT NULL,
    `description` longtext NOT NULL
);

alter table subscription add column id int unique auto_increment;

create unique index unique_subscription_meta on subscription (user_id, podcast_id);

create unique index unique_device_user_uid on device (user_id, uid);



