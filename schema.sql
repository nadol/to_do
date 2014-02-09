drop table if exists user;
create table user (
  user_id integer primary key autoincrement,
  first_name text not null,
  last_name text not null,
  email text not null,
  pw_hash text not null
);