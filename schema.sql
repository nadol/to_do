drop table if exists user;
create table user (
  id integer primary key autoincrement,
  first_name text not null,
  last_name text not null,
  email text not null,
  pw_hash text not null
);

drop table if exists project;
create table project (
  id integer primary key autoincrement,
  user_id integer not null,
  name text not null,
  description text,
  status integer not null
);

drop table if exists task;
create table task (
  id integer primary key autoincrement,
  project_id integer not null,
  name text not null,
  status integer not null
);