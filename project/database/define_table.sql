use macchine;

drop table if exists informazioni;
drop table if exists dati_manutenzione;
drop table if exists core_request_log;
drop table if exists api_request_log;
drop table if exists dati_motori;
drop table if exists dati_cilindri;
drop table if exists dati_riduttori;
drop table if exists macchinari;
drop table if exists allarmi;
drop table if exists componenti;
drop table if exists api_keys;

create table if not exists componenti(
id integer primary key auto_increment,
codiceFB varchar(255) not null unique,
cod_gestionale varchar(255) not null unique,
descrizione varchar(255) not null, -- 64KB -> 65535 char
tipo varchar(128) not null, -- meccanico / elettrico / pneumatico
quantita integer not null
);

create table if not exists manutenzioni(
id integer primary key auto_increment,
cod_manutenzione varchar(128) not null unique,
tipo varchar(128) not null,
cosa_fare text not null,
priorita varchar(32) not null,
constraint check_prorita check (priorita in ('bassa', 'normale', 'urgente')),
constraint check_tipo check (tipo in ('Ordinaria','Straordinaria'))
);

-- I dati dei motori, cilindri, riduttori si aggiornano [ALTER TABLE]
create table if not exists dati_motori(
id integer primary key auto_increment
-- temperatura, velocità(giri/min), timestamp, corrente
);
create table if not exists dati_cilindri(
id integer primary key auto_increment
-- sensore posizione, stato (esteso,chiuso), timestamp, pressione
);
create table if not exists dati_riduttori(
id integer primary key auto_increment
-- temperatura, velocità(giri/min), timestamp, coppia
);

create table if not exists allarmi(
id integer primary key auto_increment,
titolo varchar(255) not null unique,
descrizione text not null
);

create table if not exists macchinari(
id integer primary key auto_increment,
piano_produzione varchar(128) not null unique,
categoria varchar(128) not null,
tipo varchar(128) not null,
tipo_plc varchar(64) not null,
constraint check_plc check (tipo_plc in ('siemens','allen-bradly'))
);

create table if not exists api_keys(
id integer primary key auto_increment,
header varchar(255) not null unique
);

create table if not exists informazioni(
id integer primary key auto_increment,
id_macchinario integer not null,
id_allarme integer not null,
id_componente integer not null,
soluzione_problema mediumtext not null,
path_img varchar(255) not null unique,
path_video varchar(255) not null unique,
foreign key(id_macchinario) references macchinari(id) on update cascade on delete cascade,
foreign key(id_allarme) references allarmi(id) on update cascade on delete cascade,
foreign key(id_componente) references componenti(id) on update cascade on delete cascade
);

create table if not exists dati_manutenzione(
id integer primary key auto_increment,
id_motore integer not null,
id_cilindro integer not null,
id_riduttore integer not null,
id_macchinario integer not null,
foreign key(id_motore) references dati_motori(id) on update cascade on delete cascade,
foreign key(id_cilindro) references dati_cilindri(id) on update cascade on delete cascade,
foreign key(id_riduttore) references dati_riduttori(id) on update cascade on delete cascade,
foreign key(id_macchinario) references macchinari(id) on update cascade on delete cascade
);

create table if not exists api_request_logs(
id integer primary key auto_increment,
endpoint varchar(255) not null,
payload json not null,
response_status integer not null,
created_at datetime not null,
api_key integer not null,
foreign key(api_key) references api_keys(id) on update cascade on delete cascade
);

create table if not exists core_request_logs(
id integer primary key auto_increment,
endpoint varchar(255) not null,
payload json not null,
response_status integer not null,
created_at datetime not null,
api_key integer not null,
foreign key(api_key) references api_keys(id) on update cascade on delete cascade
);
