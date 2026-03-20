use macchine;

-- select * from api_request_logs;

-- alter table allarmi_soluzioni modify img varchar(255);
-- alter table allarmi_soluzioni modify video varchar(255);

alter database macchine charracter set utf8mb4 collate utf8mb4_unicode_ci;

alter table allarmi_soluzioni convert to character set utf8mb4 colate utf8mb4_unicode_ci;
