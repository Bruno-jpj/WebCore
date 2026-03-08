use macchine;

drop table if exists informazioni;
drop table if exists macchinari;
drop table if exists allarmi;
drop table if exists componenti;

create table if not exists componenti(
id integer primary key auto_increment,
descrizione_pezzo text not null -- 64KB -> 65535 char
);

create table if not exists allarmi(
id integer primary key auto_increment,
titolo varchar(255) not null unique
);

create table if not exists macchinari(
id integer primary key auto_increment,
piano_produzione varchar(128) not null unique,
categoria varchar(128) not null,
tipo varchar(128) not null
);

create table if not exists informazioni(
id integer primary key auto_increment,
id_macchinario integer not null,
id_allarme integer not null,
id_componente integer not null,
soluzione_problema mediumtext not null,
path_img varchar(255) not null unique,
path_video varchar(255) not null unique,
foreign key(id_macchinario) references macchinari(id),
foreign key(id_allarme) references allarmi(id),
foreign key(id_componente) references componenti(id)
);