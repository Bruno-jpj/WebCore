
drop database if exists macchine;
create database if not exists macchine;

use macchine;

-- User's table's
drop table if exists users;

-- API table's
drop table if exists api_request_logs;
drop table if exists core_request_logs;
drop table if exists api_keys;

-- DB table's
drop table if exists informazioni;
drop table if exists macchinari;
drop table if exists allarmi_soluzioni;

-- Users
create table if not exists users(
id bigint primary key auto_increment,
username varchar(64) not null,
pwd varchar(255) not null
);

-- API
 
create table if not exists api_keys(
id bigint primary key auto_increment,
header varchar(255) not null unique
);

create table if not exists api_request_logs(
id bigint primary key auto_increment,
endpoint varchar(255) not null,
payload json not null,
response_status integer not null,
created_at datetime not null,
api_id bigint,
foreign key(api_id) references api_keys(id) on update cascade on delete cascade
);

create table if not exists core_request_logs(
id bigint primary key auto_increment,
endpoint varchar(255) not null,
payload json not null,
response_status integer not null,
created_at datetime not null,
api_id bigint,
foreign key(api_id) references api_keys(id) on update cascade on delete cascade
);

-- DB

create table if not exists allarmi_soluzioni(
id bigint primary key auto_increment,
titolo varchar(255) not null unique,
text_it mediumtext not null,
text_eng mediumtext not null,
text_esp mediumtext,
text_de mediumtext,
text_fr mediumtext,
text_dk mediumtext,
text_pt mediumtext, 
text_ru mediumtext,
text_pl mediumtext,
text_no mediumtext, -- norvegia
text_se mediumtext, -- svezia
img varchar(255) not null,
video varchar(255) not null
);

create table if not exists macchinari(
id bigint primary key auto_increment,
piano_produzione varchar(128) not null unique,
categoria varchar(128) not null,
tipo varchar(128) not null,
tipo_plc varchar(64), -- dove c'è robot, estrusore niente PLC
constraint check_plc check (tipo_plc in ('siemens','allen-bradley','nessuno'))
);

create table if not exists informazioni(
id bigint primary key auto_increment,
id_macchinario bigint not null,
id_allarme bigint not null,
foreign key(id_macchinario) references macchinari(id) on update cascade on delete cascade,
foreign key(id_allarme) references allarmi_soluzioni(id) on update cascade on delete cascade
);

-- 1) API - research for api
create index idx_api_request_logs on api_request_logs(api_id, created_at, endpoint);
create index idx_core_request_logs on core_request_logs(api_id, created_at, endpoint);

-- 2) DB 

-- research specifics of all machine allarms
create index idx_info_machine_alarm on informazioni(id_macchinario, id_allarme);
