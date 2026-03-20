use macchine;

-- creato un utente per questo db : [username:password] => [local:FDc!3u3i3@2dD]
-- create user 'admin'@'127.0.0.1' identified by 'FDc!3u3i3@2dD';

-- create user 'lore'@'localhost' identified by 'kl!1574FTG';

use macchine;

 
-- create user 'lore'@'localhost' identified by 'kl!1574FTG';

grant all on macchine.* to 'lore'@'localhost';
grant all on test_macchine.* to 'lore'@'localhost';

flush privileges;