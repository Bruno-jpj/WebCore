use macchine;

-- User's table's
drop table if exists users;

-- API table's
drop table if exists api_request_logs;
drop table if exists core_request_logs;
drop table if exists api_keys;

-- DB table's
drop table if exists informazioni;
drop table if exists dati_manutenzione;
drop table if exists macchinari;
drop table if exists manutenzioni;
drop table if exists componenti;
drop table if exists allarmi_soluzioni;

drop table if exists dati_motori;
drop table if exists dati_macchinari;
drop table if exists dati_riduttori;

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

create table if not exists componenti(
id bigint primary key auto_increment,
nome varchar(255) not null, -- espulsore
chiave_componente varchar(255) not null unique,
codice_fb varchar(255) not null unique,
cod_gestionale varchar(255) not null unique,
descrizione varchar(255) not null, -- text type == 64KB -> 65535 char
tipo varchar(128) not null -- meccanico / elettrico / pneumatico
);

-- I dati dei motori, cilindri, riduttori si aggiornano [ALTER TABLE]
create table if not exists dati_motori(
id bigint primary key auto_increment
-- temperatura, velocità(giri/min), timestamp, corrente
);
create table if not exists dati_cilindri(
id bigint primary key auto_increment
-- sensore posizione, stato (esteso,chiuso), timestamp, pressione
);
create table if not exists dati_riduttori(
id bigint primary key auto_increment
-- temperatura, velocità(giri/min), timestamp, coppia
);

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

create table if not exists manutenzioni(
id bigint primary key auto_increment,
codice_manutenzione varchar(128) not null unique,
tipo varchar(128) not null,
priorita varchar(32) not null,
constraint check_prorita check (priorita in ('bassa', 'normale', 'urgente')),
constraint check_tipo check (tipo in ('ordinaria','straordinaria'))
);

create table if not exists macchinari(
id bigint primary key auto_increment,
piano_produzione varchar(128) not null unique,
categoria varchar(128) not null,
tipo varchar(128) not null,
tipo_plc varchar(64), -- dove c'è robot, estrusore niente PLC
id_manutenzione bigint not null,
constraint check_plc check (tipo_plc in ('siemens','allen-bradley','nessuno')),
foreign key(id_manutenzione) references manutenzioni(id)
);

create table if not exists dati_manutenzione(
id bigint primary key auto_increment,
id_motore bigint not null,
id_cilindro bigint not null,
id_riduttore bigint not null,
id_macchinario bigint not null,
id_manutenzione bigint not null,
foreign key(id_motore) references dati_motori(id) on update cascade on delete cascade,
foreign key(id_cilindro) references dati_cilindri(id) on update cascade on delete cascade,
foreign key(id_riduttore) references dati_riduttori(id) on update cascade on delete cascade,
foreign key(id_macchinario) references macchinari(id) on update cascade on delete cascade,
foreign key(id_manutenzione) references manutenzioni(id) on update cascade on delete cascade
);

create table if not exists informazioni(
id bigint primary key auto_increment,
id_macchinario bigint not null,
id_allarme bigint not null,
id_componente bigint not null,
foreign key(id_macchinario) references macchinari(id) on update cascade on delete cascade,
foreign key(id_allarme) references allarmi_soluzioni(id) on update cascade on delete cascade,
foreign key(id_componente) references componenti(id) on update cascade on delete cascade
);


-- Indexes
/*
Servono a velocizzare drasticamente il recupero dei dati, agendo come l'indice di un libro per trovare informazioni senza scansionare l'intera tabella. 
Si posizionano su colonne usate frequentemente nelle clausole WHERE, ORDER BY, GROUP BY e nei JOIN. 
Indici ben strutturati riducono i tempi di risposta da secondi a millisecondi, ma un eccesso può rallentare le operazioni di scrittura (INSERT, UPDATE). 
*/

-- 1) API - research for api
create index idx_api_request_logs on api_request_logs(api_id, created_at, endpoint);
create index idx_core_request_logs on core_request_logs(api_id, created_at, endpoint);

-- 2) DB 

-- research specifics of all machine allarms
create index idx_info_machine_alarm on informazioni(id_macchinario, id_allarme);

-- machine history
create index idx_dati_manutenzioni on dati_manutenzione(id_macchinario, id_motore, id_cilindro, id_riduttore);
create index idx_dati_motore on dati_manutenzione(id_motore);
create index idx_dati_cilindro on dati_manutenzione(id_cilindro);
create index idx_dati_riduttore on dati_manutenzione(id_riduttore);

-- Views
/*
Le views sono tabelle virtuali basate sul risultato di una SELECT memorizzata, utili per semplificare query complesse, migliorare la sicurezza nascondendo dati sensibili e presentare dati aggregati o rielaborati. 

A cosa servono le views in MySQL:
- Semplificazione: Nascondono la complessità di JOIN, UNION o calcoli complessi, permettendo di interrogare un unico oggetto.
- Sicurezza: Limitano l'accesso ai dati consentendo agli utenti di vedere solo specifiche colonne o righe di una tabella.
- Indipendenza dei dati: Permettono di cambiare la struttura delle tabelle fisiche senza rompere le applicazioni che usano la vista.
- Riuso: Memorizzano query frequenti, rendendo il codice SQL più pulito e gestibile
*/

/*
create view complete_info as
select informazioni.id as id_risposta,
macchinari.piano_produzione as piano_produzione, 
allarmi_soluzioni.titolo as titolo_allarme, 
allarmi_soluzioni.descrtext_it as soluzione,
from informazioni join macchinari on informazioni.id_macchinario = macchinari.id
join componenti on informazioni.id_componente = componenti.id
join allarmi on informazioni.id_allarme = allarmi.id
join macchinari on manutenzioni.id = macchinari.id_manutenzione;
/*