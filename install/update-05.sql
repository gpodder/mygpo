DROP TABLE IF EXISTS suggestion;
CREATE TABLE suggestion (
    user_id INT REFERENCES user (user_ptr_id),
    podcast_id INT REFERENCES podcast (id),
    priority INT,
    PRIMARY KEY(user_id, podcast_id)
);

DELIMITER $$
DROP PROCEDURE IF EXISTS update_suggestion $$
CREATE PROCEDURE update_suggestion()
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
            DELETE FROM suggestion;

            INSERT INTO suggestion select user_ptr_id, podcast_id, count(podcast_id) as priority 
                 from public_subscription, user 
                    where user_id in (select user_id from public_subscription 
                                      where podcast_id = (select min(podcast_id) from public_subscription where user_id=user_ptr_id)) 
               group by podcast_id order by priority DESC LIMIT 10;
                        
            COMMIT;
        END;
        IF deadlock=0 THEN
                LEAVE try_loop;
            ELSE
                SET attempts=attempts+1;
            END IF;
            END WHILE try_loop;

        IF deadlock=1 THEN
            call FAIL('Suggestion are not updated!');
        END IF;
        
END $$
DELIMITER ;

