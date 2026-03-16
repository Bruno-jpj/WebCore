from googletrans import Translator
from core.models import AllarmiSoluzioni

# this file was an idea of decentralizing the logic 
# but in the end I didn't like so I didn't use and left it here

class AlarmService:

    LANGUAGES = {
        "eng": "en",
        "esp": "es",
        "de": "de",
        "fr": "fr",
        "dk": "da",
        "pt": "pt",
        "ru": "ru",
        "pl": "pl",
        "no": "no",
        "se": "sv",
    }

    def __init__(self):
        self.translator = Translator()

    #
    def sync_json_to_db(self, alarm_file: dict):

        alarm_list:dict = alarm_file["lista_allarmi"]

        for title, data in alarm_list.items():

            obj, created = AllarmiSoluzioni.objects.get_or_create(
                titolo=title,
                defaults={
                    "text_it": data["testo_soluzione"]["it"],
                    "img": data["media"]["img"]["path_file"],
                    "video": data["media"]["video"]["path_file"],
                },
            )
            #
            if created:
                for lang in self.LANGUAGES:
                    setattr(
                        obj,
                        f"text_{lang}",
                        data["testo_soluzione"].get(lang)
                    )

                obj.save()

    #
    def translate(self, text):

        translations = {}

        for key, lang in self.LANGUAGES.items():

            try:
                translations[key] = self.translator.translate(
                    text,
                    src="it",
                    dest=lang
                ).text

            except Exception:
                translations[key] = None

        return translations

    #
    def create_alarm(self, title, text_it, img, video):

        translations = self.translate(text_it)

        obj = AllarmiSoluzioni.objects.create(
            titolo=title,
            text_it=text_it,
            img=img,
            video=video,
            **{f"text_{k}": v for k, v in translations.items()}
        )

        return obj, translations