use macchine;

-- select * from api_request_logs;

-- alter table allarmi_soluzioni modify img varchar(255);
-- alter table allarmi_soluzioni modify video varchar(255);

-- alter database macchine character set utf8mb4 collate utf8mb4_unicode_ci;

-- alter table allarmi_soluzioni convert to character set utf8mb4 collate utf8mb4_unicode_ci;

select titolo, piano_produzione from informazioni join allarmi_soluzioni on informazioni.id_allarme = allarmi_soluzioni.id join macchinari on informazioni.id_macchinario = macchinari.id;