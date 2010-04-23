alter table user add column deleted int (1) default 0 not null;
alter table subscription add index public (public);
