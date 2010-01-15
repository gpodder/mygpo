DELIMITER $$
DROP PROCEDURE IF EXISTS delete_inactive_users $$
CREATE PROCEDURE delete_inactive_users()
BEGIN
    DECLARE deadlock INT DEFAULT 0;
    DECLARE attempts INT DEFAULT 0;
    DECLARE done INT DEFAULT 0;
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

            delete from auth_user where is_active=0 and datediff(date(now()), date(date_joined)) > 7;

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

