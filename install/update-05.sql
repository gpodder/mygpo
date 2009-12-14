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
    DECLARE done INT DEFAULT 0;
    DECLARE user_help INT DEFAULT 0;
    DECLARE cur1 CURSOR FOR SELECT user_ptr_id FROM user;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;


    DROP TABLE IF EXISTS suggestion_pod;
    CREATE TABLE suggestion_pod (
       podID INT
    );
    DROP TABLE IF EXISTS suggestion_user;
    CREATE TABLE suggestion_user (
       userID INT
    );

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

            DELETE FROM suggestion;
            REPEAT
                FETCH cur1 INTO user_help;

            IF NOT done THEN
                    DELETE FROM suggestion_pod;
                    DELETE FROM suggestion_user;
select user_help;
                    insert into suggestion_pod (select podcast_id from public_subscription where user_id=user_help);
                    insert into suggestion_user (select user_id from public_subscription, suggestion_pod where podcast_id=podID group by user_id);
                    insert into suggestion (select user_help, podcast_id, count(podcast_id) as priority 
                                     from public_subscription, suggestion_user 
                                     where user_id=userID and podcast_id not in (select * from suggestion_pod) 
                                     group by user_help, podcast_id order by priority DESC LIMIT 10);
         
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
            call FAIL('Suggestion are not updated!');
        END IF;

        DROP TABLE IF EXISTS suggestion_user;
        DROP TABLE IF EXISTS suggestion_pod;         

END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS update_suggestion_for $$
CREATE PROCEDURE update_suggestion_for(IN user_par INT)
BEGIN
    DECLARE deadlock INT DEFAULT 0;
    DECLARE attempts INT DEFAULT 0;
        
    DROP TABLE IF EXISTS suggestion_pod;
    CREATE TABLE suggestion_pod (
       podID INT
    );
    DROP TABLE IF EXISTS suggestion_user;
    CREATE TABLE suggestion_user (
       userID INT
    );

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

            DELETE FROM suggestion where user_id=user_par;
            DELETE FROM suggestion_pod;
            DELETE FROM suggestion_user;

            insert into suggestion_pod (select podcast_id from public_subscription where user_id=user_par);
            insert into suggestion_user (select user_id from public_subscription, suggestion_pod where podcast_id=podID group by user_id);
            insert into suggestion (select user_par, podcast_id, count(podcast_id) as priority 
                                     from public_subscription, suggestion_user 
                                     where user_id=userID and podcast_id not in (select * from suggestion_pod) 
                                     group by user_par, podcast_id order by priority DESC LIMIT 10);
         
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

        DROP TABLE IF EXISTS suggestion_user;
        DROP TABLE IF EXISTS suggestion_pod;         

END $$
DELIMITER ;

