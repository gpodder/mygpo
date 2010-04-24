alter table user add column deleted int (1) default 0 not null;
alter table subscription add index public (public);

alter table episode_log add column started int(11) default null;
alter table episode_log add column total int(11) default null;


create table episode_favorites (
    id int(11) primary key auto_increment,
    episode_id int (11) not null,
    created datetime not null,
    user_id int (11) not null
);

