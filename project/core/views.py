from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt, csrf_protect, requires_csrf_token
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import logout
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.template.loader import render_to_string

from django.http import (
    Http404,
    HttpRequest,
    HttpResponse, # client GET request
    HttpResponseRedirect,
    StreamingHttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
    FileResponse
)

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

from reportlab.pdfgen import canvas, pdfimages
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate, Image

from .utils.json_manager import JsonManager

from enum import Enum
from collections import namedtuple
from googletrans import Translator 
from weasyprint import HTML
from pathlib import Path

import json
import os
import configparser
import time
import io
import csv

# Create your views here.

# HTML Template list
class TEMPLATE(Enum):
    INDEX = 'index.html'
    LOGIN = 'log_in.html'
    SIGNUP = 'sign_up.html'
    MANUAL_PAGE = 'manual.html'
    CONTACTS = 'contacts.html'
    ACCOUNT = 'account.html'
    LINE = 'line.html'
    PDF_TEMPLATE = 'alarm_solution_pdf_template.html'
#
# Index Page Logic
@check_log_in
class IndexLogic(View):
    # based on the HTTP request will do something different
    def get(self, request: HttpRequest):
        return render(request, TEMPLATE.INDEX.value)
    #
    def post(self, request: HttpRequest):
        return render(request, TEMPLATE.INDEX.value)
    #
    def delete(self, request: HttpRequest):
        return render(request, TEMPLATE.INDEX.value)
    #
    def put(self, request: HttpRequest):
        return render(request, TEMPLATE.INDEX.value)
# Login View
def login(request: HttpRequest):
    
    # check if the request method is POST
    if request.method == "POST":
        
        # take from request the username & password - see the HTML form for the names
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        # try to check if the username exists and the password is correct for that username
        try:
            
            # create a user obj if exists
            user = Users.objects.get(username=username)
            
            # check the hashed passwords (inserted, saved)
            if check_password(password, user.pwd):
                
                # put the user.id into the Django session table
                request.session['user_id'] = user.id
                
                # redirect to the Index View
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
        # check if the request method is POST
        if request.method == "POST":
            
            # take the input data from the POST request
            in_username = request.POST.get("username")
            password1 = request.POST.get("password1")
            password2 = request.POST.get("password2")
            
            # check if all data where inserted
            if not all([in_username, password1, password2]):
                messages.error(request, "INFO: Tutti i campi devono essere compilati")
                return redirect('signup')
           
            # check if the 2 pwd are equal
            if password1 != password2:
                messages.error(request, "INFO: Le 2 password non corrispondono")
                return redirect('signup')
            
            # check if exists a username with the same username
            if Users.objects.filter(username = in_username).exists():
                messages.error(request, "INFO: Lo username scelto già esiste")
                return redirect('signup')
            
            # hash the password and try to create the user
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
def logout_view(request: HttpRequest):
    
    # Remove the authenticated user's ID from the request and flush their session data. - I can do the same thing in the Admin panel
    logout(request)
    return redirect("login")
#
# Manual Page Logic
class ManualLogic(View): 

    # define the JSON file path - it doesn't like relative path - 
    JSON_PATH = settings.DATA_ROOT / "allarmi_soluzioni.json"
    CONF_PATH = settings.DATA_ROOT / "conf.json"
    JSON_BACK_PATH = settings.DATA_ROOT / "allarmi_soluzioni_backup.json"
    
    JM = JsonManager(JSON_PATH, CONF_PATH, JSON_BACK_PATH)

    def get(self, request: HttpRequest):
        
        # load JSON file
        cfg_file: dict = self.JM.read_conf()
        alarm_file: dict = self.JM.read_alarm_json()
        
        # give a default language 
        chosen_language = request.GET.get('language', 'text_it')

        # take all element from the DB table and all JSON key alarm title
        alarm_queryset = AllarmiSoluzioni.objects.all()
        alarm_json_set = set(alarm_file["lista_allarmi"])

        # check the number of element of DB table and JSON key
        alarm_db_count = alarm_queryset.count()
        alarm_json_count = len(alarm_json_set)
        
        print(f"Database: {alarm_db_count} | JSON: {alarm_json_count}")

        # check the DB element with JSON file and in case upload: Sync JSON -> DB
        if (alarm_db_count == alarm_json_count) and ((cfg_file["db_update"] == 'true') and (cfg_file["json_update"] == 'true')):
            
            messages.info(request, f"INFO: Trovato {alarm_db_count} elementi nel DB")

            # if one of the 2 is 0 - try to load them
            if (alarm_db_count == 0 or alarm_json_count == 0):
                messages.info(request, f"INFO: Elementi nel DB {alarm_db_count} | nel JSON {alarm_json_count}")
                messages.info(request, "INFO: Inizio procedura di recupero")
                
                # set conf var to false so it doens't pass the first if-check
                cfg_file["db_update"] == 'false'
                cfg_file["json_update"] == 'false'
                
                # read + load backup JSON file 
                alarm_file: dict = self.JM.read_backup_json()
                
                # pass the backup JSON file to the alarm_JSON and pass the dict to the local-var
                alarm_file: dict = self.JM.write_alarm_json(alarm_file)
        #
        # check if the key in the JSON are more than the KEY in the DB
        elif alarm_db_count < alarm_json_count:
            try:
                # upload JSON data into the DB
                self.upload_json(alarm_file)

                # pass the conf var to True
                cfg_file['json_update'] = 'true'
                cfg_file['db_update'] = 'true'
                
                self.JM.write_conf(cfg_file)

            except Exception as e:
                messages.error(request, f"Errore upload: {e}")
                
            finally:
                messages.info(request, "INFO: Finito...Ricarica la pagina e controlla i risultati...")
        else:
            # caso incoerenza DB > JSON
            
            # delete all the element in the table
            alarm_queryset.delete()

            cfg_file['json_update'] = 'false'
            cfg_file['db_update'] = 'false'

            messages.warning(request, "DB resettato. Ricarica la pagina.")

        # init search form
        search_form = SearchAlarmsForm(request.GET)

        # declare the dict to pass it to the context
        alarm_queryset_filtered = None

        # check if the form return no errors
        if search_form.is_valid():
            
            # Is a dictionary that contains the validated and converted values from a submitted form after it has passed validation.
            # It is only available after you call form.is_valid() — otherwise it will not exist or will be empty.
            search_text = search_form.cleaned_data.get("search_text")

            if search_text:
                
                # put into the session the search_text from the search-bar
                # in this case is not a table but a value which exists only in the session
                request.session['search_text'] = search_text

                # search the string is contained, it's case-insensitive and it performs a partial match
                alarm_queryset_filtered = alarm_queryset.filter(
                    titolo__icontains = search_text
                    ) 
        else:
            # reset the form
            search_form = SearchAlarmsForm()

        # Search all DB data - need a name in the HTML btn and a value to check
        if request.GET.get("all") is not None:
            alarm_queryset_filtered = alarm_queryset

        # put into the session the chosen language from the drop-down menu in the manual.html
        request.session['chosen_language'] = chosen_language

        # pass the context to the page
        context = {
            'search_form': search_form,
            'alarms_filtered': alarm_queryset_filtered,
            'chosen_language': chosen_language,
            'language_dict': LanguageModel.LANGUAGE_CHOICE.items()
        }

        return render(request, TEMPLATE.MANUAL_PAGE.value, context)
    #
    def post(self, request: HttpRequest):
        
        # load JSON file
        cfg_file: dict = self.JM.read_conf()
        alarm_file: dict = self.JM.read_alarm_json()
        
        # take all data from the POST request - insert form manual.html
        title = request.POST.get("alarm_title")
        solution_text = request.POST.get("solution_text")
        img = request.FILES.get("solution_img")
        video = request.FILES.get("solution_video")
        
        # take all data from the POST request - check the checkbox HTML value 
        alarm_checkBox = request.POST.get("chk_alarm")
        solution_checkBox = request.POST.get("chk_solution")
        img_checkBox = request.POST.get("chk_img")
        video_checkBox = request.POST.get("chk_video") # taking the last element
        
        # alarm check_box when updating / deleting
        alarm_list: list = request.POST.getlist("aa_checkBox") # taking the entire list
        
        # created a dict with the values taken from the chekbox
        chk_dict = {
            'alarm': alarm_checkBox,
            'solution': solution_checkBox,
            'img': img_checkBox,
            'video': video_checkBox
        }
        
        # take the request name from the button in the form
        # if is not 'action' it will return error in the code below
        action = request.POST.get('action')        
        
        try:
            # check the value of action
            if action == 'add':
                
                # check if all fields aren't empty
                if not all([title, solution_text, img, video]):

                    messages.info(request, "INFO: Tutti i campi devo essere riempiti")
                    return redirect(request.path)
                else:
                    # call add func
                    self.add_alarm(request, title, solution_text, img, video, alarm_file)
            elif action == 'delete':
                
                # call delete func
                self.delete_alarm(request, title, alarm_file, alarm_list)
            elif action == 'update': 
                
                # take from the session the value from the GET def
                search_title = request.session.get('search_text')

                # call the update
                self.update_alarm(request, search_title, title, solution_text, img, video, chk_dict, alarm_list)
                
                # after updating flush the session
                del request.session['search_text']
            elif action == 'download':
                
                # take the values from the session from the GET def
                search_title = request.session.get('search_text')
                chosen_language = request.session.get('chosen_language')

                # call the func and return the result
                return self.create_download_pdf(request, alarm_list, chosen_language)
                # del request.session['search_text']
            #
        except Exception as e:
            messages.error(request, f"ERROR: POST Exception [{e}]")

        return redirect(request.path)
    #
    def upload_json(self, alarm_file: dict):
        
        # create a set of the key of the JSON dict
        alarm_set = set(alarm_file["lista_allarmi"])

        for alarm_name in alarm_set:
            try: 
                # search if the alarm exists in the DB
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
        
        # check if the alarm exists both in the DB or JSON file
        if AllarmiSoluzioni.objects.filter(titolo=title).exists() or title in alarm_set:
            messages.info(request, "Allarme già presente nel DB / JSON")
            return

        # define google translator
        translator = Translator()

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
            # cycle for every key:value pair
            for key, lang in languages.items():
                
                # populate the dict with the key:value 
                # value => solution_text will be translated in every language from the languages dict
                translations[key] = translator.translate(
                    solution_text,
                    src='it',
                    dest=lang
                ).text
        except Exception:
            messages.warning(request, "Errore traduzione automatica")

        # insert into DB and creation of an obj to do logic later
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
        SAME THING OF WRITING:
        
        new_dict = {}

        for k, v in translations.items():
            new_dict[f"text_{k}"] = v
        '''

        print(f"Creato allarme: {obj.titolo}")
        try:
            # Updating JSON file...
            alarm_file["lista_allarmi"][title] = {
                "media": {
                    "video": {
                        "nome_file": obj.video.name,
                        "path_file": obj.video.path
                        },
                    "img": {
                        "nome_file": obj.img.name,
                        "path_file": obj.img.path
                        }
                },
                "testo_soluzione": {
                    "it": solution_text,
                    **translations
                }
            }
            # ...and pushing 
            self.JM.write_alarm_json(alarm_file)
        except Exception as e:
            print(f"Nooooooooooooo: {e}")
            
        messages.success(request, "Allarme creato correttamente")
    #
    def update_alarm(self, request: HttpRequest, search_title, title, solution_text, img, video, chk_dict: dict, alarm_list):
        
        # IN ANY CASE YOU WANT THE USER TO UPDATE THE ALARMS WITH THE SEARCH-TITLE BAR JUST CHANGE 'aa_checkBox' WITH 'search_title'
        
        alarm_list_value = alarm_list[0]
        
        qs = AllarmiSoluzioni.objects.filter(titolo=alarm_list_value)

        if not qs.exists():
            messages.info(request, "L'allarme selezionato non esiste nel DB")
            return

        fields_to_update = {}
        
        # CHECK TITLE - OK
        if chk_dict.get("alarm") and title:
            fields_to_update["titolo"] = title

        # CHECK SOLUTION - OK
        # Problem:
        ### if you don't do the search with the correct name the session pass the wrong allarm name and it doesn't work
        if chk_dict.get("solution") and solution_text:
            fields_to_update["text_it"] = solution_text
            
            # Traduzioni
            translator = Translator()
            languages = {
                "eng": "en", "esp": "es", "de": "de", "fr": "fr",
                "dk": "da", "pt": "pt", "ru": "ru", "pl": "pl",
                "no": "no", "se": "sv"
            }

            translations = {}

            try:
                for key, lang in languages.items():
                    
                    translations[key] = translator.translate(solution_text, src='it', dest=lang).text
                    
                fields_to_update.update({f"text_{k}": v for k, v in translations.items()})
            except Exception:
                messages.warning(request, "Errore traduzione automatica")

        # CHECK IMG - OK
        if chk_dict.get("img") and img:
            fields_to_update["img"] = img

        # CHECK VIDEO - OK
        if chk_dict.get("video") and video:
            fields_to_update["video"] = video

        # Execute update only if there are fields to update
        if fields_to_update:
            qs.update(**fields_to_update)
            messages.success(request, "Allarme aggiornato correttamente")
        else:
            messages.info(request, "Nessun campo selezionato o fornito da aggiornare")
    # 
    def delete_alarm(self, request: HttpRequest, title, alarm_file, alarm_list):
        
        # IN ANY CASE YOU WANT THE USER TO DELETE THE ALARMS WITH THE INSERT-TITLE BAR JUST CHANGE 'aa_checkBox' WITH 'title'

        alarm_set = set(alarm_file["lista_allarmi"])
        
        alarm_list_value = alarm_list[0]

        if alarm_list_value in alarm_set and AllarmiSoluzioni.objects.filter(titolo = alarm_list_value).exists():

            messages.info(request, "Allarme presente sia nel DB e nel JSON")

            try:
                AllarmiSoluzioni.objects.get(titolo = alarm_list_value).delete()

                del alarm_file["lista_allarmi"][alarm_list_value]

                self.JM.write_alarm_json(alarm_file)
            except AllarmiSoluzioni.DoesNotExist:
                messages.info(request, "INFO: L'allarme che si vuole eliminare non è stato trovato nel DB")
            finally:
                messages.info(request, "Allarme eliminato sia nel DB e nel JSON")
        else:
            messages.info(request, "Allarme non presente sia nel DB che nel JSON")
    
    # TODO: CHECK logica
    def create_download_pdf(self, request: HttpRequest, alarm_list: list, chosen_language):
        
        alarms_data = []
        
        for t in alarm_list:
            alarm = AllarmiSoluzioni.objects.filter(titolo = t).first()
            
            if not alarm:
                continue
            
            alarms_data.append({
                "titolo": alarm.titolo,
                "solution": getattr(alarm, chosen_language),
                "img": request.build_absolute_uri(alarm.img.url) if alarm.img else None
            })
            
            # request.build_absolute_uri(alarm.img.url) → http://127.0.0.1:8000/media/img_name.jpg
            # print(f"immagine_path:  {request.build_absolute_uri(alarm.img.url) if alarm.img else None}")
            
        html_string = render_to_string(
            TEMPLATE.PDF_TEMPLATE.value,
            {"alarms": alarms_data}
        )
        
        pdf_file = io.BytesIO()
        
        HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(pdf_file)
        
        pdf_file.seek(0)
        
        return FileResponse(
            pdf_file,
            content_type="application/pdf",
            headers={'Content-Dispostion': 'attachment; filename="allarmi_soluzioni.pdf" '}
        )
        
    # TODO: check why it doesn't work 
    def create_download_csv(self, request: HttpRequest, search_title):

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="alarms.csv"'

        writer = csv.writer(response)

        # header
        writer.writerow(["title", "solution"])

        alarms = AllarmiSoluzioni.objects.all()

        for a in alarms:
            writer.writerow([a.titolo, a.text_it])

        return response
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