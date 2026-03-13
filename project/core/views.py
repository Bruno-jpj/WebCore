from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt, csrf_protect, requires_csrf_token
from django.contrib.auth.hashers import make_password, check_password
# from django.contrib.auth import logout
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin

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

from .forms import (
    SearchAlarmsForm, 
    ChoseLanguage
)

from .models import (
    Macchinari,
    Informazioni,
    AllarmiSoluzioni,
    Componenti,
    Users,
    LanguageModel
)

from .utils.json_manager import JsonManager

from enum import Enum
from collections import namedtuple
from googletrans import Translator

import json
import configparser
import time

# Create your views here.

# HTML Template
class TEMPLATE(Enum):
    INDEX = 'index.html'
    LOGIN = 'log_in.html'
    SIGNUP = 'sign_up.html'
    MANUAL_PAGE = 'manual.html'
    CONTACTS = 'contacts.html'
    ACCOUNT = 'account.html'
    LINE = 'line.html'
#
# Index Page Logic
class IndexLogic(View):
    def get(self, request: HttpRequest):
        return render(request, TEMPLATE.INDEX.value)
    #
    def post(self, request: HttpRequest):
        #
        return render(request, TEMPLATE.INDEX.value)
    #
# Login
def login(request: HttpRequest):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        try:
            user = Users.objects.get(username=username)
            if check_password(password, user.pwd):
                request.session['user_id'] = user.id
                return redirect('index')
            else:
                messages.error(request, "Username o Password errati")
        except Users.DoesNotExist:
            messages.error(request, "Username o Password inesistenti")
        return redirect('login')
    return render(request, TEMPLATE.LOGIN.value)
# Signup
def signup(request: HttpRequest):
    try:
        if request.method == "POST":
            in_username = request.POST.get("username")
            password1 = request.POST.get("password1")
            password2 = request.POST.get("password2")
            #
            if not all([in_username, password1, password2]):
                messages.error(request, "INFO: Tutti i campi devono essere compilati")
                return redirect('signup')
            #
            if password1 != password2:
                messages.error(request, "INFO: Le 2 password non corrispondono")
                return redirect('signup')
            #
            if Users.objects.filter(username = in_username).exists():
                messages.error(request, "INFO: Lo username scelto già esiste")
                return redirect('signup')
            #
            try:
                hased_pwd = make_password(password1)

                Users.objects.create(
                    username = in_username,
                    pwd = hased_pwd
                )

                messages.success(request, "INFO: Utente creato con successo")
                return redirect('login')
            except Exception as e:
                print(f"ERRORE: Utente-Create non riuscito: [{e}]")
                messages.error(request, "INFO: Errore nella creazione dell'utente, riprovare più tardi")
    except Exception as e:
        print(f"ERRORE: Utente-SignUp non riuscito: [{e}]")
        messages.error(request, "INFO: Errore nella creazione dell'utente, riprovare più tardi")
    return render(request, TEMPLATE.SIGNUP.value)
# Logout
def logout(request: HttpRequest):
    # logout(request)
    return redirect("login")
#
# Manual Page Logic
class ManualLogic(View): 

    JSON_PATH = r'C:\Users\loren\Desktop\GitHub\WebCore\project\allarmi_soluzioni.json'
    CONF_PATH = r'C:\Users\loren\Desktop\GitHub\WebCore\project\conf.json'

    JM = JsonManager(JSON_PATH, CONF_PATH)

    def get(self, request: HttpRequest):

        # load JSON file
        cfg_file: dict = self.JM.read_conf()
        alarm_file: dict = self.JM.read_alarm_json()
        
        chosen_language = request.GET.get('language', 'text_it')

        # take all element from the DB table and all JSON key alarm title
        alarm_queryset = AllarmiSoluzioni.objects.all()
        alarm_json_set = set(alarm_file["lista_allarmi"])

        # check the number of element of DB table and JSON key
        alarm_db_count = alarm_queryset.count()
        alarm_json_count = len(alarm_json_set)

        # check the DB element with JSON file and in case upload: Sync JSON -> DB
        if (alarm_db_count == alarm_json_count) and ((cfg_file["db_update"] == 'true') and (cfg_file["json_update"] == 'true')):
            
            messages.info(request, f"INFO: Trovato {alarm_db_count} elementi nel DB")
        
        elif alarm_db_count < alarm_json_count:
            try:
                self.upload_json(alarm_file)

                cfg_file['json_update'] = 'true'
                cfg_file['db_update'] = 'true'

                self.JM.write_conf(cfg_file)

            except Exception as e:
                messages.error(request, f"Errore upload: {e}")
                
            finally:
                messages.info(request, "INFO: Finito...Ricarica la pagina e controlla i risultati...")
        else:
            # caso incoerenza DB > JSON
            alarm_queryset.delete()

            cfg_file['json_update'] = 'false'
            cfg_file['db_update'] = 'false'

            messages.warning(request, "DB resettato. Ricarica la pagina.")

        # Search form
        search_form = SearchAlarmsForm(request.GET)

        alarm_queryset_filtered = None

        if search_form.is_valid():
            search_text = search_form.cleaned_data.get("search_text")

            if search_text:
                # search the string is contained, it's case-insensitive and it performs a partial match
                alarm_queryset_filtered = alarm_queryset.filter(
                    titolo__icontains = search_text
                    ) 
        else:
            search_form = SearchAlarmsForm()

         # Search all DB data - need a name in the html btn and a value to check
         # request.GET.get("value")
        if request.GET.get("all") is not None:
            alarm_queryset_filtered = alarm_queryset

        # pass the context
        context = {
            'search_form': search_form,
            'alarms_filtered': alarm_queryset_filtered,
            'chosen_language': chosen_language
        }

        return render(request, TEMPLATE.MANUAL_PAGE.value, context)
    #
    def post(self, request: HttpRequest):
        # load JSON file
        cfg_file: dict = self.JM.read_conf()
        alarm_file: dict = self.JM.read_alarm_json()
        #
        title = request.POST.get("alarm_title")
        solution_text = request.POST.get("solution_text")
        img = request.FILES.get("solution_img")
        video = request.FILES.get("solution_video")
        #        
        action = request.POST.get('action')

        try:
            if action == 'add':

                if not all([title, solution_text, img, video]):

                    messages.info(request, "INFO: Tutti i campi devo essere riempiti")
                    return redirect(request.path)
                else:
                    self.add_alarm(request, title, solution_text, img, video, alarm_file)
            
            elif action == 'delete':
                self.delete_alarm(request, title, alarm_file)
            
            elif action == 'update':
                self.update_alarm(request, title, solution_text, img, video)
            
            elif action == 'download':
                return HttpResponse("Download non implementato")
            #
        except Exception as e:
            messages.error(request, f"ERROR: POST Exception [{e}]")

        return redirect(request.path)
    #
    def upload_json(self, alarm_file: dict):
        alarm_set = set(alarm_file["lista_allarmi"])

        for alarm_name in alarm_set:
            try: 
                temp_obj = AllarmiSoluzioni.objects.get(titolo = alarm_name)
                print(f"Già esiste: [{temp_obj}]")
            except AllarmiSoluzioni.DoesNotExist:
                try:
                    # create the object and auto-save it
                    AllarmiSoluzioni.objects.create(
                        titolo = alarm_name,
                        text_it = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["it"],
                        text_eng = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["eng"],
                        text_esp = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["esp"],
                        text_de = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["de"],
                        text_fr = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["fr"],
                        text_dk = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["dk"],
                        text_pt = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["pt"],
                        text_ru = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["ru"],
                        text_pl = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["pl"],
                        text_no = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["no"],
                        text_se = alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["se"],
                        img = alarm_file["lista_allarmi"][alarm_name]["media"]["img"]["path_file"],
                        video = alarm_file["lista_allarmi"][alarm_name]["media"]["video"]["path_file"]
                        )
                    #
                except Exception as e:
                    print(f"Upload from Json Except: [{e}]")
        #
        '''
        STESSA COSA SCRITTA SOPRA FORSE MEGLIO: 

        for alarm_name in alarm_set:
            obj, created = AllarmiSoluzioni.objects.get_or_create(
                titolo=alarm_name,
                defaults={
                    "text_it": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["it"],
                    "text_eng": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["eng"],
                    "text_esp": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["esp"],
                    "text_de": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["de"],
                    "text_fr": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["fr"],
                    "text_dk": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["dk"],
                    "text_pt": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["pt"],
                    "text_ru": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["ru"],
                    "text_pl": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["pl"],
                    "text_no": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["no"],
                    "text_se": alarm_file["lista_allarmi"][alarm_name]["testo_soluzione"]["se"],
                    "img": alarm_file["lista_allarmi"][alarm_name]["media"]["img"]["path_file"],
                    "video": alarm_file["lista_allarmi"][alarm_name]["media"]["video"]["path_file"]
                }
            )
            if created:
                print(f"Creato nuovo allarme: [{obj.titolo}]")
            else:
                print(f"Gia esiste: [{obj.titolo}]")
        '''
    #
    def add_alarm(self, request: HttpRequest, title, solution_text, img, video, alarm_file: dict):
        
        alarm_set = set(alarm_file["lista_allarmi"])
        
        if AllarmiSoluzioni.objects.filter(titolo=title).exists() or title in alarm_set:
            messages.info(request, "Allarme già presente nel DB / JSON")
            return

        translator = Translator()

        translations: dict = {}

        # lingue da tradurre
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
                translations[key] = translator.translate(
                    solution_text,
                    src='it',
                    dest=lang
                ).text
        except Exception:
            messages.warning(request, "Errore traduzione automatica")

        # creazione DB-obj
        obj = AllarmiSoluzioni.objects.create(
            titolo=title,
            text_it=solution_text,
            img=img,
            video=video,
            **{f"text_{k}": v for k, v in translations.items()} 
        )

        # translations.items() => (key, value) -> (language, text) == (eng, hello)
        # f"text_{k}" → crea la nuova chiave (text_eng)
        '''
        LA STESSA DI SCRIVERE:
        new_dict = {}

        for k, v in translations.items():
            new_dict[f"text_{k}"] = v
        '''

        print(f"Creato allarme: {obj.titolo}")

        # aggiornamento JSON
        alarm_file["lista_allarmi"][title] = {
            "media": {
                "video": {
                    "nome_file": "aaaa",
                    "path_file": str(video)},
                "img": {
                    "nome_file": "aaaa",
                    "path_file": str(img)}
            },
            "testo_soluzione": {
                "it": solution_text,
                **translations
            }
        }

        self.JM.write_alarm_json(alarm_file)

        messages.success(request, "Allarme creato correttamente")

        
    # TODO: DA PROGRAMMARE -> forse aggiungo una pagina
    def update_alarm(self, request: HttpRequest, title, solution_text, img, video, alarm_file):
        
        alarm_set = set(alarm_file["lista_allarmi"])

        if title in alarm_set and AllarmiSoluzioni.objects.filter(titolo = title).exists():

            messages.info(request, "Allarme presente sia nel DB e nel JSON")
            
            alarm_obj = AllarmiSoluzioni.objects.get(titolo = title)

            

    # 
    def delete_alarm(self, request: HttpRequest, title, alarm_file):

        alarm_set = set(alarm_file["lista_allarmi"])

        if title in alarm_set and AllarmiSoluzioni.objects.filter(titolo = title).exists():

            messages.info(request, "Allarme presente sia nel DB e nel JSON")

            try:
                AllarmiSoluzioni.objects.get(titolo = title).delete()

                del alarm_file["lista_allarmi"][title]

                self.JM.write_alarm_json(alarm_file)
            except AllarmiSoluzioni.DoesNotExist:
                messages.info(request, "INFO: L'allarme che si vuole eliminare non è stato trovato nel DB")
            finally:
                messages.info(request, "Allarme eliminato sia nel DB e nel JSON")
        else:
            messages.info(request, "Allarme non presente sia nel DB che nel JSON")
    #
    def download_alarm(self):
        pass
    #
#
# Contacts Page Logic
def contacts(request: HttpRequest):
    return render(request, TEMPLATE.CONTACTS.value)
# Account Page Logic
def account(request: HttpRequest):
    return render(request, TEMPLATE.ACCOUNT.value)
# Line Page Logic
def line(request: HttpRequest):
    return render(request, TEMPLATE.LINE.value)