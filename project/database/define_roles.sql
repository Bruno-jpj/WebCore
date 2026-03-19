use macchine;

-- creato un utente per questo db : [username:password] => [local:FDc!3u3i3@2dD]
-- create user 'admin'@'127.0.0.1' identified by 'FDc!3u3i3@2dD';

-- create user 'loren'@'localhost' identified by 'kl!1574FTG';

-- grant select, delete, update, insert, etc..
grant all on macchine.* to 'loren'@'localhost';
-- grant all on *.* to 'admin'@'127.0.0.1';

flush privileges;