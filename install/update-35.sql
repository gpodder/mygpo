alter table episode add column mimetype varchar(30);
create index mimetype on episode(mimetype);

