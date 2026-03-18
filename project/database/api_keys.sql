use macchine;

/*
insert into api_keys(header) values
('api-key-test0'),
('YR83Bd&Bl3JomAuZ'),
('Ji$XM}Y({foVf*Ab'),
('sna*ma<rVl2qE!ms'),
('ww^Hv}4qwm>Y_jqh'),
('?<(N&Jk)L>LsblwX'),
('gy80CB-9$sCN)gXf'),
('G)-G92@Y}L344Uc{'),
('qquD|H)E*&HA]5Lf'),
('8I0sHuNIA{qqerQ5'),
('eNFJ+)PHKqC.gx^='),
('l(V{P=6shD<>pm*P'),
('>!0*TC1=ur1(+vG&'),
('%<@:4r-3}U=J}Es6'),
('-2u7?]x9<hHDR)^o'),
('J!g9_Ir(^b!@3R2L');
*/

select * from api_request_logs;

select header, endpoint, response_status, created_at from api_request_logs join api_keys on api_request_logs.api_id = api_keys.id;