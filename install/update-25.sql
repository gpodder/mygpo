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
                        ORDER BY subscription_count DESC);

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

