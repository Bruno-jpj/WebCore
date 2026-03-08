use macchine;

insert into allarmi(titolo) values
('temperatura'),
('sensore');

insert into macchinari(piano_produzione, categoria, tipo) values
('pp23240', 'TR', '600'),
('pp23342', 'TR', '1200'),
('pp23332', 'DR', '800'),
('pp21000', 'DR', '600'),
('pp26547', 'TR', '2000'),
('pp24550', 'DR', '4000'),
('pp25255', 'TR', '1600');

insert into componenti(descrizione_pezzo) values
('dispositivo robusto progettato per convertire la temperatura in un segnale elettrico misurabile (resistenza, tensione, corrente o digitale) per il monitoraggio e controllo dei processi. Le tecnologie principali includono termoresistenze (PT100/PT1000) per alta precisione, termocoppie per range estremi, termistori (NTC/PTC) e sensori a infrarossi per misurazioni senza contatto'),
('Un sensore di posizione industriale è un dispositivo elettronico o elettromeccanico progettato per misurare e monitorare la posizione fisica, lo spostamento lineare o la rotazione angolare di un oggetto all interno di un sistema automatizzato');

insert into informazioni(id_macchinario, id_allarme, id_componente, soluzione_problema, path_img, path_video) values
(1, 1, 1, 'sostituzione pezzo','C:\Users\loren\Desktop\GitHub\WebCore\project\static\img\sensore_laser.png','C:\Users\loren\Desktop\GitHub\WebCore\project\static\videos\video_sensore.mp4');