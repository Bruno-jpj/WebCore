from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt, csrf_protect, requires_csrf_token
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import logout
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

from enum import Enum
from collections import namedtuple
from googletrans import Translator

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
    ACCOUNT = 'account.html'
    LINE = 'line.html'
#
# Index Page Logic
class IndexLogic(View):
    def get(self, request: HttpRequest):
        return render(request, TEMPLATE.INDEX.value)
    #
    def post(self, request: HttpRequest):
        try:                
            choice = request.POST.get('redirect')
            if choice == 'account':
                return redirect('account')
            elif choice == 'line':
                return redirect('line')
            elif choice == 'contacts':
                return redirect('contacts')
            elif choice == 'manual':
                return redirect('manual')
            elif choice == 'logout':
                return redirect('logout')
            else:
                messages.error(request, "Form Error. Please try again.")
                return render(request, 'index')
        except Exception as e:
            messages.error(request, f"Error n. {e}")
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
    logout(request)
    return redirect("login")
#
# Manual Page Logic
class ManualLogic(View):
    class LANGUAGE(Enum):
        IT = 'it'
        EN = 'en'
        ESP = 'esp'
        FR = 'fr'
        DE = 'de'
        PT = 'pt' # portoghese
        FI = 'fi' # finlandese
        SE = 'se' # svedese
        NR = 'nr' # norvegese
        PL = 'pl' # polacco
        DK = 'dk' # danese
        RU = 'ru'
    
    JSON_PATH = r'C:\Users\loren\Desktop\GitHub\WebCore\project\allarmi_soluzioni.json'
    CONF_PATH = r'C:\Users\loren\Desktop\GitHub\WebCore\project\conf.json'

    def get(self, request: HttpRequest):
        # load JSON file
        cfg_file: dict = self.read_cfg_json()
        alarm_file: dict = self.read_alarm_json()

        json_key, db_key = 'json_update', 'db_update'
        chosen_language = request.GET.get('language', 'text_it')

        # take all element from the DB table and all JSON key alarm title
        alarm_queryset = AllarmiSoluzioni.objects.all()
        alarm_json_set = set(alarm_file["lista_allarmi"])

        # check the number of element of DB table and JSON key
        alarm_db_count = alarm_queryset.count()
        alarm_json_count = len(alarm_json_set)

        # check the DB element with JSON file and in case upload: JSON -> DB
        if (alarm_db_count == alarm_json_count) and ((cfg_file["db_update"] == 'true') and (cfg_file["json_update"] == 'true')):
            
            print(f"INFO: Trovato: [{alarm_db_count}] elementi nel DB...")

            messages.info(request, f"INFO: Trovato {alarm_db_count} elementi nel DB")
        elif alarm_db_count < alarm_json_count:
            try:
                self.upload_json(alarm_file)

                cfg_file['json_update'] = 'true'
                cfg_file['db_update'] = 'true'

                with open(self.CONF_PATH, 'w') as file:
                    cfg_file = json.dump(cfg_file, file, indent=4)

            except Exception as e:
                print(f"Upload Func Error: [{e}]")
            finally:
                print("Finito...Ricarica la pagina e controlla i risultati...")
                messages.info(request, "INFO: Finito...Ricarica la pagina e controlla i risultati...")
        else:
            print("Condizione: [count(db_element==json_element) and (conf.json == true)] non rispettata delete di tutte le righe della tabella AlarmSolution")
            print("Ricarica la pagina...\nVerrà eseguito un Upload dal JSON nel DB e cambiate le flag di conf.json.")
            alarm_queryset.delete()
        # take language from the page


        # search alarm-title logic
        ## Gestione form di ricerca separata
        search_form = SearchAlarmsForm(request.GET)
        alarm_queryset_filtered = None
        if search_form.is_valid() and search_form.cleaned_data.get("search_text"):
            search_text = search_form.cleaned_data["search_text"]
            # search the string is contained, it's case-insensitive and it performs a partial match
            alarm_queryset_filtered = alarm_queryset.filter(titolo__icontains=search_text) 
        else:
            search_form = SearchAlarmsForm()

        # pass the context
        context = {
            'show_all': False,
            'search_form': search_form,
            'alarms_filtered': alarm_queryset_filtered,
            'language_list': '',
            'chosen_language': chosen_language
        }

        return render(request, TEMPLATE.MANUAL_PAGE.value, context)
    #
    def post(self, request: HttpRequest):
        # load JSON file
        cfg_file: dict = self.read_cfg_json()
        alarm_file: dict = self.read_alarm_json()
        #
        try:
            title = request.POST.get("alarm_title")
            solution_text = request.POST.get("solution_text")
            img = request.FILES.get("solution_img")
            video = request.FILES.get("solution_video")
            #
            if not all([title, solution_text, img, video]):
                messages.info(request, "INFO: Tutti i campi devo essere riempiti")
            else:
                choice = request.POST.get('action')
                if choice == 'update':
                    return HttpResponse("DEVO FINIRE DI PROGRAMMARLO...MANCA LA LOGICA DI COSA VUOI CAMBIARE...")
                elif choice == 'add':
                    self.add_alarm(request, title, solution_text, img, video, alarm_file)
                elif choice == 'delete':
                    self.delete_alarm(request, title, alarm_file)
                elif choice == 'download':
                    return HttpResponse("Non Programmato")
            #
        except Exception as e:
            messages.error(request, f"ERROR: [{e}]")
    #
    def read_cfg_json(self) -> dict:
        with open(self.CONF_PATH, 'r') as file:
            cfg_dict = json.load(file)
        return cfg_dict
    #
    def read_alarm_json(self) -> dict:
        with open(self.JSON_PATH, 'r') as file:
            alm_dict = json.load(file)
        return alm_dict
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
        
        translator = Translator()

        if title in alarm_set and AllarmiSoluzioni.objects.get(titolo = title):
            messages.info(request, "Allarme già presente sia nel DB e nel JSON")
        else:
            try:
                text_eng = translator.translate(solution_text, src='it', dest='en')
                text_esp = translator.translate(solution_text, src='it', dest='es')
                text_de = translator.translate(solution_text, src='it', dest='de')
                text_fr = translator.translate(solution_text, src='it', dest='fr')
                text_dk = translator.translate(solution_text, src='it', dest='dk')
                text_pt = translator.translate(solution_text, src='it', dest='pt')
                text_ru = translator.translate(solution_text, src='it', dest='ru')
                text_pl = translator.translate(solution_text, src='it', dest='pl')
                text_no = translator.translate(solution_text, src='it', dest='no')
                text_se = translator.translate(solution_text, src='it', dest='se')
            except Exception as e:
                print("Error: Auto-translating")
            finally:
                print("Done Trying auto-translating")
            #
            try:
                AllarmiSoluzioni.objects.create(
                    titolo = title,
                    text_it = solution_text,
                    text_eng = text_eng,
                    text_esp = text_esp,
                    text_de = text_de,
                    text_fr = text_fr,
                    text_dk = text_dk,
                    text_pt = text_pt,
                    text_ru = text_ru,
                    text_pl = text_pl,
                    text_no = text_no,
                    text_se = text_se,
                    img = img,
                    video = video
                    )
                print("INFO: Created AllarmiSoluzioni object")
            except Exception as e:
                print(f"Error creating new AllarmiSoluzioni object: [{e}]")
                messages.error(request, "INFO: Errore nella traduzione automatica o creazione dell'allarme ")
            finally:
                print("Done Trying cretaing AllarmiSoluzioni object")
            #
            try:
                alarm_file["lista_allarmi"][title] = {
                    "media":{
                        "video":{
                            "nome_file":"aaaa",
                            "path_file":video
                        },
                        "img":{
                            "nome_file":"aaaa",
                            "path_file":img
                        }
                    },
                    "testo_soluzione":{
                        "it": solution_text,
                        "eng": text_eng,
                        "esp": text_esp,
                        "de": text_de,
                        "fr": text_fr,
                        "dk": text_dk,
                        "pt": text_pt,
                        "ru": text_ru,
                        "pl": text_pl,
                        "no": text_no,
                        "se": text_se,
                    }
                }
                with open(self.JSON_PATH, 'w+') as file:
                    json.dump(alarm_file, file, indent=4)
            except Exception as e:
                print(f"Error creating new Alarm JSON object: [{e}]")
                messages.error(request, "INFO: Errore nella traduzione automatica o creazione dell'allarme ")
            finally:
                print("Done Trying inserting into the conf.json")  
    # TODO: DA FINIRE DI PROGRAMMARE UPDATE, MANCA LA LOGICA DI SCELTA DI COSA AGGIORNARE
    def update_alarm(self, request: HttpRequest, title, solution_text, img, video, alarm_file):
        
        alarm_set = set(alarm_file["lista_allarmi"])
        
        if title in alarm_set and AllarmiSoluzioni.objects.get(titolo = title):
            messages.info(request, "Allarme presente sia nel DB e nel JSON")
            #
            try:
                translator = Translator()
                # alter table
                AllarmiSoluzioni.objects.update(
                    titolo = title,
                    text_it = solution_text,
                    text_eng = translator.translate(solution_text, src='it', dest='en'),
                    text_esp = translator.translate(solution_text, src='it', dest='es'),
                    text_de = translator.translate(solution_text, src='it', dest='de'),
                    text_fr = translator.translate(solution_text, src='it', dest='fr'),
                    text_dk = translator.translate(solution_text, src='it', dest='dk'),
                    text_pt = translator.translate(solution_text, src='it', dest='pt'),
                    text_ru = translator.translate(solution_text, src='it', dest='ru'),
                    text_pl = translator.translate(solution_text, src='it', dest='pl'),
                    text_no = translator.translate(solution_text, src='it', dest='no'),
                    text_se = translator.translate(solution_text, src='it', dest='se'),
                    img = img,
                    video = video
                )
            except Exception as e:
                print(f"Error updating existing AllarmiSoluzioni object: [{e}]")
                messages.error(request, "INFO: Errore nella traduzione automatica o aggiornamento dell'allarme ")
            finally:
                print("Done Trying cretaing AllarmiSoluzioni object")
        else:
            messages.info(request, "Allarme presente sia nel DB e nel JSON")
    # 
    def delete_alarm(self, request: HttpRequest, title, alarm_file):

        alarm_set = set(alarm_file["lista_allarmi"])

        if title in alarm_set and AllarmiSoluzioni.objects.get(titolo = title):
            messages.info(request, "Allarme presente sia nel DB e nel JSON")
            try:
                AllarmiSoluzioni.objects.get(titolo = title).delete()
                removed_value = alarm_set.pop(title)
                print(f"Removed value: [{removed_value}]")
                with open(self.JSON_PATH, 'w') as file:
                    json.dump(alarm_set, file, indent=4)
            except AllarmiSoluzioni.DoesNotExist:
                messages.info(request, "INFO: L'allarme che si vuole eliminare non è stato trovato nel DB")
            finally:
                messages.info(request, "Allarme eliminato sia nel DB e nel JSON")
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