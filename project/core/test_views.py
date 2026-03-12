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
class AlarmPage(View):
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
    #
    JSON_PATH = r'C:\Users\loren\Desktop\GitHub\WebCore\project\script\json\allarmi_soluzioni.json'
    CONF_PATH = r'C:\Users\loren\Desktop\GitHub\WebCore\project\conf.json'

    json_update = None
    db_update = None

    def get(self, request: HttpRequest):

        # read the json files
        cfg_dict: dict = self.read_conf_json(request)
        alarm_dict: dict = self.read_alarm_json(request)

        # take all elements from the tabel -> return a QuerySet
        alarm_solution_queryset = AllarmiSoluzioni.objects.all()
        
        # check if found at least one element in the table
        db_num_alarm = alarm_solution_queryset.count()

        # check found number of element in the JSON
        json_num_alarm = len(set(alarm_dict["lista_allarmi"]))     

        # take the chosen language for the alarm-text
        chosen_language = request.GET.get('language', '') # ('name select or btn', value passata) ==> valori del btn nell'html

        # Search Form Logic - if search_text in the request get type (in the URL)
        # Gestione form di ricerca separata
        search_form = SearchAlarmsForm(request.GET)
        if search_form.is_valid() and search_form.cleaned_data.get("search_text"):
            search_text = search_form.cleaned_data["search_text"]
            # search the string is contained, it's case-insensitive and it performs a partial match
            alarm_solution_queryset = alarm_solution_queryset.filter(titolo__icontains=search_text) 
        else:
            search_form = SearchAlarmsForm()


        if db_num_alarm >= json_num_alarm:
            print(f"INFO: Trovato: [{db_num_alarm}] elementi nel DB...")
            messages.info(request, f"INFO: Trovato {db_num_alarm} elementi nel DB")
        else:
            print(f"INFO: Trovato: [{db_num_alarm}] elementi nel DB...")
            messages.info(request, "INFO: Nessun elemento trovato... Inizio Upload da file di configurazione...")
            try:
                self.upload_from_json(alarm_dict)
            except Exception as e:
                print(f"Upload Func Error: [{e}]")
            finally:
                print("Finito...Controlla i risultati...")
        #
        context = {
            'alarms': alarm_solution_queryset,
            'language_list' : ChoseLanguage.Meta.fields,
            'chosen_language': chosen_language,
            'search_form': search_form
        }
        
        return render(request, TEMPLATE.ALARM_PAGE.value, context)
    #
    def post(self, request: HttpRequest):
        
        try:
            alarm_title = request.POST.get("alarm_title")
            solution_text = request.POST.get("solution_text")
            img_file = request.FILES.get("solution_img")
            video_file = request.FILES.get("solution_video")
            #
            if not all([alarm_title, solution_text, img_file, video_file]):
                messages.info(request, "INFO: Tutti i campi devono essere compilati...")
                return redirect('alarm_page')
            #
            if AllarmiSoluzioni.objects.filter(titolo = alarm_title).exists():
                messages.info(request, "INFO: Allarme già esistente")
                return redirect('alarm_page')
            #
            try:
                pass
            except Exception as e:
                pass
            #            
        except Exception as e:    
            return HttpResponse(f"Btn non programmato ancora...{e}")
    #
    def read_conf_json(self, request: HttpRequest) -> dict:
        with open(self.CONF_PATH, 'r') as file:
            cfg_dict: dict = json.load(file)

        return cfg_dict
    #
    def read_alarm_json(self, request: HttpRequest) -> dict:

        # read and transform to python dict
        with open(self.JSON_PATH, 'r') as file:
            alarm_dict: dict = json.load(file)

        return alarm_dict
    #
    def upload_from_json(self, alarm_dict: dict):
        
        # set with only the alarm titles
        alarm_set = set(alarm_dict["lista_allarmi"])

        # print(f"len: [{len(alarm_set)}]")

        for alarm_name in alarm_set:
            try: 
                temp_obj = AllarmiSoluzioni.objects.get(titolo = alarm_name)
                print(f"Già esiste: [{temp_obj}]")
            except AllarmiSoluzioni.DoesNotExist:
                try:
                    # create the object and auto-save it
                    AllarmiSoluzioni.objects.create(
                        titolo = alarm_name,
                        text_it = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["it"],
                        text_eng = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["eng"],
                        text_esp = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["esp"],
                        text_de = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["de"],
                        text_fr = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["fr"],
                        text_dk = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["dk"],
                        text_pt = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["pt"],
                        text_ru = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["ru"],
                        text_pl = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["pl"],
                        text_no = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["no"],
                        text_se = alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["se"],
                        img = alarm_dict["lista_allarmi"][alarm_name]["media"]["img"]["path_file"],
                        video = alarm_dict["lista_allarmi"][alarm_name]["media"]["video"]["path_file"]
                        )
                    #
                except Exception as e:
                    print(f"Upload from Json Except: [{e}]")
            else:
                print(f"Gia esiste: [{temp_obj}]")
        #
        '''
        STESSA COSA SCRITTA SOPRA FORSE MEGLIO: 

        for alarm_name in alarm_set:
            obj, created = AllarmiSoluzioni.objects.get_or_create(
                titolo=alarm_name,
                defaults={
                    "text_it": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["it"],
                    "text_eng": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["eng"],
                    "text_esp": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["esp"],
                    "text_de": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["de"],
                    "text_fr": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["fr"],
                    "text_dk": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["dk"],
                    "text_pt": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["pt"],
                    "text_ru": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["ru"],
                    "text_pl": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["pl"],
                    "text_no": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["no"],
                    "text_se": alarm_dict["lista_allarmi"][alarm_name]["testo_soluzione"]["se"],
                    "img": alarm_dict["lista_allarmi"][alarm_name]["media"]["img"]["path_file"],
                    "video": alarm_dict["lista_allarmi"][alarm_name]["media"]["video"]["path_file"]
                }
            )
            if created:
                print(f"Creato nuovo allarme: [{obj.titolo}]")
            else:
                print(f"Gia esiste: [{obj.titolo}]")
        '''          

