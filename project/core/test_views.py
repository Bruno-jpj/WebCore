from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt, csrf_protect, requires_csrf_token
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User


from django.http import (
    Http404,
    HttpRequest,
    HttpResponse, # client GET request
    HttpResponseRedirect,
    StreamingHttpResponse,
    HttpResponseBadRequest,
    JsonResponse
)

# to decorate a def() just apply it
# if want to use it on CBV need to integrate: method_decorator
from .decorators import  check_log_in

from .forms import SearchAlarmsForm, ChoseLanguage

from .models import (
    Macchinari,
    Informazioni,
    AllarmiSoluzioni,
    Componenti,
    Users,
    LanguageModel
)

from api.serializers import InformazioniSerializers

from enum import Enum
from collections import namedtuple

import json
import configparser

# Create your views here.

# HTML Template
class TEMPLATE(Enum):
    INDEX = 'index.html'
    LOGIN = 'log_in.html'
    SIGNUP = 'sign_up.html'
    MANUAL_PAGE = 'manual.html'
    CONTACTS = 'contacts.html'
    ACCOUNT = 'account.hmtl'
    LINE = 'line.html'    
#


# WebApp views
class IndexLogic(LoginRequiredMixin, View):

    login_url = "login"

    def get(self, request):
        return render(request, TEMPLATE.INDEX.value)

    def post(self, request):
        return render(request, TEMPLATE.INDEX.value)
#
def login(request: HttpRequest):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect("index")

        messages.error(request, "Username o password errati")

    return render(request, TEMPLATE.LOGIN.value)
#
def signup(request: HttpRequest):

    if request.method == "POST":

        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Le password non corrispondono")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username già esistente")
            return redirect("signup")

        User.objects.create_user(
            username=username,
            password=password1
        )

        messages.success(request, "Utente creato")
        return redirect("login")

    return render(request, TEMPLATE.SIGNUP.value)
#
def logout_view(request):
    logout(request)
    return redirect("login")
#

# -----------------------------------------
# -----------------------------------------
# -----------------------------------------

#
class ManualLogic(View):

    # Enum per gestire le lingue disponibili
    class LANGUAGE(Enum):
        IT = 'it'
        EN = 'en'
        ESP = 'esp'
        FR = 'fr'
        DE = 'de'
        PT = 'pt'
        FI = 'fi'
        SE = 'se'
        NR = 'nr'
        PL = 'pl'
        DK = 'dk'
        RU = 'ru'

    # Percorsi file JSON
    JSON_PATH = r'C:\Users\loren\Desktop\GitHub\WebCore\project\allarmi_soluzioni.json'
    CONF_PATH = r'C:\Users\loren\Desktop\GitHub\WebCore\project\conf.json'

    # ---------------------------
    # GET
    # ---------------------------
    def get(self, request: HttpRequest):

        # carico configurazioni
        cfg_file = self.read_cfg_json()
        alarm_file = self.read_alarm_json()

        chosen_language = request.GET.get('language', 'text_it')

        alarm_queryset = AllarmiSoluzioni.objects.all()
        alarm_json_set = set(alarm_file["lista_allarmi"])

        alarm_db_count = alarm_queryset.count()
        alarm_json_count = len(alarm_json_set)

        # ---------------------------
        # Sync JSON -> DB
        # ---------------------------
        if alarm_db_count == alarm_json_count and \
           cfg_file["db_update"] == 'true' and \
           cfg_file["json_update"] == 'true':

            messages.info(request, f"Trovati {alarm_db_count} elementi nel DB")

        elif alarm_db_count < alarm_json_count:

            try:
                self.upload_json(alarm_file)

                cfg_file['json_update'] = 'true'
                cfg_file['db_update'] = 'true'

                with open(self.CONF_PATH, 'w') as file:
                    json.dump(cfg_file, file, indent=4)

                messages.info(request, "Upload JSON -> DB completato")

            except Exception as e:
                messages.error(request, f"Errore upload: {e}")

        else:
            # caso incoerenza DB > JSON
            alarm_queryset.delete()
            messages.warning(request, "DB resettato. Ricarica la pagina.")

        # ---------------------------
        # Search form
        # ---------------------------
        search_form = SearchAlarmsForm(request.GET)

        alarm_queryset_filtered = None

        if search_form.is_valid():
            search_text = search_form.cleaned_data.get("search_text")

            if search_text:
                alarm_queryset_filtered = alarm_queryset.filter(
                    titolo__icontains=search_text
                )

        # context template
        context = {
            'show_all': False,
            'search_form': search_form,
            'alarms_filtered': alarm_queryset_filtered,
            'chosen_language': chosen_language
        }

        return render(request, TEMPLATE.MANUAL_PAGE.value, context)

    # ---------------------------
    # POST
    # ---------------------------
    def post(self, request: HttpRequest):

        alarm_file = self.read_alarm_json()

        title = request.POST.get("alarm_title")
        solution_text = request.POST.get("solution_text")
        img = request.FILES.get("solution_img")
        video = request.FILES.get("solution_video")

        if not all([title, solution_text, img, video]):
            messages.info(request, "Tutti i campi devono essere compilati")
            return redirect(request.path)

        action = request.POST.get('action')

        try:

            if action == 'add':
                self.add_alarm(request, title, solution_text, img, video, alarm_file)

            elif action == 'delete':
                self.delete_alarm(request, title, alarm_file)

            elif action == 'update':
                return HttpResponse("Logica update non implementata")

            elif action == 'download':
                return HttpResponse("Download non implementato")

        except Exception as e:
            messages.error(request, f"Errore: {e}")

        return redirect(request.path)

    # ---------------------------
    # READ CONFIG JSON
    # ---------------------------
    def read_cfg_json(self) -> dict:
        with open(self.CONF_PATH, 'r') as file:
            return json.load(file)

    # ---------------------------
    # READ ALARM JSON
    # ---------------------------
    def read_alarm_json(self) -> dict:
        with open(self.JSON_PATH, 'r') as file:
            return json.load(file)

    # ---------------------------
    # UPLOAD JSON -> DB
    # ---------------------------
    def upload_json(self, alarm_file: dict):

        alarm_set = set(alarm_file["lista_allarmi"])

        for alarm_name in alarm_set:

            data = alarm_file["lista_allarmi"][alarm_name]

            obj, created = AllarmiSoluzioni.objects.get_or_create(
                titolo=alarm_name,
                defaults={
                    "text_it": data["testo_soluzione"]["it"],
                    "text_eng": data["testo_soluzione"]["eng"],
                    "text_esp": data["testo_soluzione"]["esp"],
                    "text_de": data["testo_soluzione"]["de"],
                    "text_fr": data["testo_soluzione"]["fr"],
                    "text_dk": data["testo_soluzione"]["dk"],
                    "text_pt": data["testo_soluzione"]["pt"],
                    "text_ru": data["testo_soluzione"]["ru"],
                    "text_pl": data["testo_soluzione"]["pl"],
                    "text_no": data["testo_soluzione"]["no"],
                    "text_se": data["testo_soluzione"]["se"],
                    "img": data["media"]["img"]["path_file"],
                    "video": data["media"]["video"]["path_file"],
                }
            )

            if created:
                print(f"Creato nuovo allarme: {obj.titolo}")
            else:
                print(f"Allarme già esistente: {obj.titolo}")

    # ---------------------------
    # ADD ALARM
    # ---------------------------
    def add_alarm(self, request, title, solution_text, img, video, alarm_file):

        if AllarmiSoluzioni.objects.filter(titolo=title).exists():
            messages.info(request, "Allarme già presente nel DB")
            return

        translator = Translator()

        # lingue da tradurre
        languages = {
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

        translations = {}

        try:
            for key, lang in languages.items():
                translations[key] = translator.translate(
                    solution_text,
                    src='it',
                    dest=lang
                ).text
        except Exception:
            messages.warning(request, "Errore traduzione automatica")

        # creazione DB
        obj = AllarmiSoluzioni.objects.create(
            titolo=title,
            text_it=solution_text,
            img=img,
            video=video,
            **{f"text_{k}": v for k, v in translations.items()}
        )

        print(f"Creato allarme: {obj.titolo}")

        # aggiornamento JSON
        alarm_file["lista_allarmi"][title] = {
            "media": {
                "video": {"path_file": str(video)},
                "img": {"path_file": str(img)}
            },
            "testo_soluzione": {
                "it": solution_text,
                **translations
            }
        }

        with open(self.JSON_PATH, 'w') as file:
            json.dump(alarm_file, file, indent=4)

        messages.success(request, "Allarme creato correttamente")


# ---------------------------------
#
# ----------------------------------

from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages

from utils.json_manager import JsonManager
from services.alarm_service import AlarmService


class ManualLogic(View):

    JSON_PATH = r"C:\project\allarmi_soluzioni.json"
    CONF_PATH = r"C:\project\conf.json"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.json_manager = JsonManager(self.JSON_PATH, self.CONF_PATH)
        self.alarm_service = AlarmService()

    # -------------------------
    # GET
    # -------------------------
    def get(self, request):

        alarm_file = self.json_manager.read_alarm_json()

        queryset = AllarmiSoluzioni.objects.all()

        search_form = SearchAlarmsForm(request.GET)

        filtered = None

        if search_form.is_valid():
            text = search_form.cleaned_data.get("search_text")

            if text:
                filtered = queryset.filter(titolo__icontains=text)

        context = {
            "search_form": search_form,
            "alarms_filtered": filtered,
        }

        return render(request, TEMPLATE.MANUAL_PAGE.value, context)

    # -------------------------
    # POST
    # -------------------------
    def post(self, request):

        title = request.POST.get("alarm_title")
        solution_text = request.POST.get("solution_text")
        img = request.FILES.get("solution_img")
        video = request.FILES.get("solution_video")

        if not all([title, solution_text, img, video]):
            messages.error(request, "Campi mancanti")
            return redirect(request.path)

        try:

            obj, translations = self.alarm_service.create_alarm(
                title,
                solution_text,
                img,
                video
            )

            alarm_file = self.json_manager.read_alarm_json()

            alarm_file["lista_allarmi"][title] = {
                "media": {
                    "video": {"path_file": str(video)},
                    "img": {"path_file": str(img)}
                },
                "testo_soluzione": {
                    "it": solution_text,
                    **translations
                }
            }

            self.json_manager.write_alarm_json(alarm_file)

            messages.success(request, "Allarme creato")

        except Exception as e:
            messages.error(request, str(e))

        return redirect(request.path)