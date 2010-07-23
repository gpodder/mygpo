alter table episode add column mimetype varchar(30);
create index mimetype on episode(mimetype);

alter table podcast add column content_types varchar(30);
create index content_types on podcast(content_types);

alter table episode change timestamp timestamp datetime null;

