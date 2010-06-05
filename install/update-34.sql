BEGIN;
CREATE TABLE `search_searchentry` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `text` longtext NOT NULL,
    `obj_type` varchar(20) NOT NULL,
    `obj_id` integer NOT NULL,
    `tags` varchar(200) NOT NULL,
    `priority` integer NOT NULL
)
;
COMMIT;

create fulltext index search_text on search_searchentry (text);
create index search_objtype on search_searchentry (obj_type);
create index search_objid on search_searchentry (obj_id);
create index search_tags on search_searchentry (tags);
create index search_priority on search_searchentry (priority);

