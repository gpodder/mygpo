alter table podcast_tags modify source varchar(100);
alter table podcast_tags add unique index unique_tag (tag, podcast_id, source, user_id);

alter table podcast_tags add index tag (tag);
alter table podcast_tags add index source (source);

alter table podcast_tags convert to character set utf8 collate utf8_general_ci;
