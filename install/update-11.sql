DELIMITER $$
DROP PROCEDURE IF EXISTS update_suggestion $$
CREATE PROCEDURE update_suggestion()
BEGIN
    DECLARE deadlock INT DEFAULT 0;
    DECLARE attempts INT DEFAULT 0;
    DECLARE done INT DEFAULT 0;
    DECLARE user_help INT DEFAULT 0;
    DECLARE pod_count INT DEFAULT 0;
    DECLARE cur1 CURSOR FOR SELECT user_ptr_id FROM user where suggestion_up_to_date = 0;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;
    
    CREATE TEMPORARY TABLE suggestion_pod (
       podID INT
    );
    
    CREATE TEMPORARY TABLE suggestion_user (
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

            REPEAT
                FETCH cur1 INTO user_help;

                IF NOT done THEN
                    DELETE FROM suggestion where user_id=user_help;
                    DELETE FROM suggestion_pod;
                    DELETE FROM suggestion_user;
select user_help;
                    insert into suggestion_pod (select podcast_id from current_subscription where user_id=user_help);

                    SELECT count(*) into pod_count FROM suggestion_pod;

                    IF pod_count > 0 THEN
                        insert into suggestion_user (select user_id from public_subscription, suggestion_pod where podcast_id=podID group by user_id);
                        insert into suggestion (select user_help, podcast_id, count(podcast_id) as priority, NULL 
                                     from public_subscription, suggestion_user 
                                     where user_id=userID and podcast_id not in (select * from suggestion_pod) 
                                     group by user_help, podcast_id order by priority DESC LIMIT 10);
                    ELSE
                        insert into suggestion (select user_help, podcast_id, subscription_count, NULL as priority from toplist 
                                     group by user_help, podcast_id order by subscription_count DESC LIMIT 10);
                    END IF;
                    update user set suggestion_up_to_date = 1 where user_ptr_id = user_help;
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

END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS update_suggestion_for $$
CREATE PROCEDURE update_suggestion_for(IN user_par INT)
BEGIN
    DECLARE deadlock INT DEFAULT 0;
    DECLARE attempts INT DEFAULT 0;
    DECLARE pod_count INT DEFAULT 0;
    DECLARE utd INT DEFAULT 0;
        
    CREATE TEMPORARY TABLE suggestion_pod (
       podID INT
    );
    
    CREATE TEMPORARY TABLE suggestion_user (
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
            SELECT suggestion_up_to_date into utd FROM user where user_ptr_id = user_par;
            IF utd < 1 THEN
               DELETE FROM suggestion where user_id=user_par;
               DELETE FROM suggestion_pod;
               DELETE FROM suggestion_user;

               insert into suggestion_pod (select podcast_id from current_subscription where user_id=user_par);
	    
               SELECT count(*) into pod_count FROM suggestion_pod;

               IF pod_count > 0 THEN
                  insert into suggestion_user (select user_id from public_subscription, suggestion_pod where podcast_id=podID group by user_id);
                  insert into suggestion (select user_par, podcast_id, count(podcast_id) as priority, NULL 
                                     from public_subscription, suggestion_user 
                                     where user_id=userID and podcast_id not in (select * from suggestion_pod) 
                                     group by user_par, podcast_id order by priority DESC LIMIT 10);
               ELSE
                  insert into suggestion (select user_par, podcast_id, subscription_count, NULL as priority from toplist 
                  group by user_par, podcast_id order by subscription_count DESC LIMIT 10);
               END IF;
               update user set suggestion_up_to_date = 1 where user_ptr_id = user_par;
            END IF;
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

DELIMITER $$
DROP PROCEDURE IF EXISTS update_toplist $$
CREATE PROCEDURE update_toplist()
BEGIN
    DECLARE deadlock INT DEFAULT 0;
    DECLARE attempts INT DEFAULT 0;

    CREATE TEMPORARY TABLE toplist_temp (
            podcast_id INT PRIMARY KEY REFERENCES podcast (id),
            subscription_count INT NOT NULL DEFAULT 0,
            old_place INT DEFAULT 0,
            INDEX(podcast_id)
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
            DELETE FROM toplist_temp;
            INSERT INTO toplist_temp (SELECT a.podcast_id, COUNT(*) AS count_subscription, 
                                       COALESCE((select (id - (select min(id) from toplist) + 1) from toplist where podcast_id = a.podcast_id),0)
                        FROM (SELECT DISTINCT podcast_id, user_id
                            FROM public_subscription) a
                        GROUP BY podcast_id);
            DELETE FROM toplist;
            INSERT INTO toplist (podcast_id, subscription_count, id, old_place) (SELECT podcast_id, subscription_count, NULL, old_place FROM toplist_temp
                        ORDER BY subscription_count DESC LIMIT 100);

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

DROP TABLE IF EXISTS podcast_tags;
CREATE TABLE podcast_tags (
    id INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    tag VARCHAR(100) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
    podcast_id INT NOT NULL,
    source VARCHAR(1000) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
    user_id INT,
    weight INT,
    FOREIGN KEY (user_id) REFERENCES auth_user (id),
    FOREIGN KEY (podcast_id) REFERENCES podcast (id)
);

