from deep_translator import GoogleTranslator, MicrosoftTranslator, ChatGptTranslator
from deep_translator.exceptions import TooManyRequests, TranslationNotFound

class TESTAllarmiSoluzioni():
    id = ""
    titolo = ""
    text_it = ""
    text_eng = ""
    text_esp = ""
    text_de = ""
    text_fr = ""
    text_dk = ""
    text_pt = ""
    text_ru = ""
    text_pl = ""
    text_no = ""
    text_se = ""
    img = ""
    video = ""
#

SOLUTION = "sono un testo di prova, spero di essere tradotto bene."

def auto_translate():
    
    translations: dict = {}
    
    # dict with the languages
    languages: dict = {
        "eng": "en",
        "esp": "es",
        "de": "de",
        "fr": "fr",
        "dk": "da",
        "pt": "pt",
        "ru": "ru",
        "pl": "pl",
        "no": "no",
        "se": "sv"
    }
    try:
        for key, lang in languages.items():
            translations[key] = GoogleTranslator(source='it', target=lang).translate(SOLUTION)
    except TranslationNotFound:
        raise RuntimeError("Translation could not be found. Check language codes or text")
    except Exception as e:
        raise RuntimeError(f"uncaught error: {e}")
    
    return translations

def main():
    translations: dict = auto_translate()
    
    trans: dict = {}
    
    print(translations.items())
    
    
    
    
    print("allarme creato con successo")

if __name__ == "__main__":
    main()