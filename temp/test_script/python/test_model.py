import json
import time


from deep_translator import GoogleTranslator

old_json = r'/var/www/webcore/test_script/json/attivita_testi.json'
new_json = r'/var/www/webcore/test_script/json/test.json'


def copy_json():
    
    '''
    text = open("file.json").read()
    clean = ''.join(c for c in text if ord(c) >= 32)
    data = json.loads(clean)
    '''
    
    # leggo il file vecchio
    with open(old_json, 'r') as file:
        clean = ''.join(c for c in file if ord(c) >= 32)
        old_data_title: dict = json.load()
        
    titoli_list: list = list(old_data_title.keys())
    # print(titoli_list)

    with open(new_json, 'r') as file:
        new_data_title: dict = json.load(file)

    for t in titoli_list:
        new_data_title["lista_allarmi"][t] = {
            "media":{
                    "video":{
                        "nome_file":"",
                        "path_file":""
                    },
                    "img":{
                        "nome_file":"",
                        "path_file":""
                    }
                },
            "testo_soluzione":{
                "it":"",
                "eng":"",
                "esp":"",
                "de":"",
                "fr":"",
                "dk":"",
                "pt":"",
                "ru":"",
                "pl":"",
                "no":"",
                "se":""
            }
        }
        with open(new_json, 'w') as file:
            json.dump(new_data_title, file, indent=4)
        #
    print("OK")
#
def insert_tries():
    
    # leggo il file vecchio
    with open(old_json, 'r') as f:
        old_alarm_json_file: dict = json.load(f)
        
    # leggo il file nuovo
    with open(new_json, 'r') as file:
        alarm_json_file: dict = json.load(file)
    
    # creo una lista con i titoli allarmi / attività    
    titoli_list: list = list(alarm_json_file.keys())
        
    for t in titoli_list:
        
        if old_alarm_json_file["testi"][t]["testo"]["it"] is not None or old_alarm_json_file["testi"][t]["testo"] is not None:
            
            solution_text = old_alarm_json_file["testi"][t]["testo"]["it"]
            
            trans_eng=GoogleTranslator(source='it', target='en').translate(solution_text)
            trans_esp=GoogleTranslator(source='it', target='es').translate(solution_text)
            trans_de=GoogleTranslator(source='it', target='de').translate(solution_text)
            trans_fr=GoogleTranslator(source='it', target='fr').translate(solution_text)
            trans_dk=GoogleTranslator(source='it', target='da').translate(solution_text)
            trans_pt=GoogleTranslator(source='it', target='pt').translate(solution_text)
            trans_ru=GoogleTranslator(source='it', target='ru').translate(solution_text)
            trans_pl=GoogleTranslator(source='it', target='pl').translate(solution_text)
            trans_no=GoogleTranslator(source='it', target='no').translate(solution_text)
            trans_se=GoogleTranslator(source='it', target='sv').translate(solution_text)
            
            
            alarm_json_file["lista_allarmi"][t]["testo_soluzione"] = {
                
                "it" : solution_text,
                "eng" : trans_eng,
                "esp" : trans_esp,
                "de" : trans_de,
                "fr" : trans_fr,
                "dk" : trans_dk,
                "pt" : trans_pt,
                "ru" : trans_ru,
                "pl" : trans_pl,
                "no" : trans_no,
                "se" : trans_se
            }
        else:
            print(f"Allarme: [{t}] non ha un testo 'it' \n")
        #
        with open(new_json,'w+') as file:
            alarm_json_file = json.dump(alarm_json_file, file, indent=4)
    print("Finito Controlla...")
#
# NON USARE SOVRASSCRIVE ANCHE LE KEY DOVE TROVA IL TESTO
def update_translations():

    # --- LOAD FILES (SAFE) ---
    try:
        with open(old_json, "r") as f:
            raw = f.read()
            #raw = f.read(20)  # leggi i primi 20 byte
            # print(raw)
    except json.JSONDecodeError as e:
        print(f"Errore JSON nel file OLD: {e}")
        return
    
    # trasforma i \n in newline reali
    # raw = raw.replace("\\n", "").replace("\\r", "")

    # ora JSON valido
    old_alarm_json_file = json.loads(raw)

    try:
        with open(new_json, "r", encoding="utf-8") as f:
            alarm_json_file: dict = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Errore JSON nel file NEW: {e}")
        return

    # --- CONFIG ---
    langs = ["en", "es", "de", "fr", "da", "pt", "ru", "pl", "no", "sv"]

    translators = {
        lang: GoogleTranslator(source='it', target=lang)
        for lang in langs
    }

    def safe_translate(translator, text, lang, retries=5):
        for _ in range(retries):
            try:
                translated = translator.translate(text)

                # controllo fallback (traduzione identica o vuota)
                if not translated or translated.strip().lower() == text.strip().lower():
                    raise ValueError(f"Traduzione sospetta [{lang}]")

                return translated

            except Exception:
                time.sleep(0.5)

        print(f"Fallback su IT per lingua [{lang}]")
        return text

    # --- LOOP ---
    lista_allarmi = alarm_json_file.get("lista_allarmi", {})
    testi_vecchi = old_alarm_json_file.get("testi", {})

    for t in lista_allarmi.keys():

        testo = testi_vecchi.get(t, {}).get("testo", {})
        solution_text = testo.get("it")

        if not solution_text:
            print(f"Allarme [{t}] senza testo IT")
            continue
        
        
        # --- CLEAN NEWLINES ONLY IN STRING ---
        # solution_text = solution_text.replace("\r\n", "").replace("\r", "").replace("\n", "")
        
        translations = {}

        for lang, translator in translators.items():
            translations[lang] = safe_translate(translator, solution_text, lang)
            time.sleep(0.8)  # evita rate limit

        # aggiorno JSON in sicurezza
        if t not in lista_allarmi:
            continue

        lista_allarmi[t]["testo_soluzione"] = {
            "it": solution_text,
            **translations
        }

    # --- SAVE (UNA SOLA VOLTA) ---
    try:
        with open(new_json, "w", encoding="utf-8") as f:
            json.dump(alarm_json_file, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Errore scrittura file: {e}")
        return

    print("Finito. Controlla i risultati.")
#
def insert_macchinari():
    pass
#
def insert_informazioni():
    pass
#
if __name__ == "__main__":
    update_translations()