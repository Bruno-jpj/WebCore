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
from django.db import transaction

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

from ...project.core.decorators import  check_log_in

from ...project.core.forms import (
    SearchAlarmsForm, 
    ChoseLanguage
)

from ...project.core.models import (
    AllarmiSoluzioni,
    Users,
    LanguageModel
)

from ...project.core.services.json_manager import JsonManager
from deep_translator import GoogleTranslator
from deep_translator.exceptions import TranslationNotFound

from enum import Enum
from collections import namedtuple

from weasyprint import HTML # questa libreria funziona solo sotto OS linux su windows bisogna installare 'gtk3.exe' ed installare poi la lib weasyprint
from pathlib import Path
from datetime import datetime, timezone

import json
import os
import configparser
import time
import io
import csv


@check_log_in
class ManualAdminLogic(View): 

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
        
        # print(f"Database: {alarm_db_count} | JSON: {alarm_json_count}")
        logger_view(alarm_db_count, "Numero elementi DB")
        logger_view(alarm_json_count, "Numero elementi JSON")

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

        return render(request, TEMPLATE.MANUAL_ADMIN_LOGIC.value, context)
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
                if not all([title, solution_text]):

                    messages.info(request, "INFO: Almeno Titolo e Soluzione devono essere riempiti")
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
                #print(f"Già esiste: [{temp_obj}]")
                logger_view(temp_obj, "Già esiste questo allarme")

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
                    #print(f"Upload from Json Except: [{e}]")
                    logger_view(e, "Upload from Json Except")
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

        try:
            eng=GoogleTranslator(source='it', target='en').translate(solution_text)
            esp=GoogleTranslator(source='it', target='es').translate(solution_text)
            de=GoogleTranslator(source='it', target='de').translate(solution_text)
            fr=GoogleTranslator(source='it', target='fr').translate(solution_text)
            dk=GoogleTranslator(source='it', target='da').translate(solution_text)
            pt=GoogleTranslator(source='it', target='pt').translate(solution_text)
            ru=GoogleTranslator(source='it', target='ru').translate(solution_text)
            pl=GoogleTranslator(source='it', target='pl').translate(solution_text)
            no=GoogleTranslator(source='it', target='no').translate(solution_text)
            se=GoogleTranslator(source='it', target='sv').translate(solution_text)
        except TranslationNotFound as t:
            logger_view(t, "ERROR: Traduzione automatica nel add_alarm")
        
        # insert into DB and creation of an obj to do logic later
        obj = AllarmiSoluzioni.objects.create(
            titolo=title,
            text_it=solution_text,
            text_eng=eng,
            text_esp=esp,
            text_de=de,
            text_fr=fr,
            text_dk=dk,
            text_pt=pt,
            text_ru=ru,
            text_pl=pl,
            text_no=no,
            text_se=se,
            img=img,
            video=video,
        )

        # translations.items() => (key, value) -> (language, text) == (eng, hello)
        # f"text_{k}" → crea la nuova chiave (text_eng)

        # print(f"Creato allarme: {obj.titolo}")
        
        try:
            # Updating JSON file...
            alarm_file["lista_allarmi"][title] = {
                "media": {
                    "video": {
                        "nome_file": getattr(obj.video, 'name', "None File") if obj.video else "None File",
                        "path_file": getattr(obj.video, 'path', "None File") if obj.video else "None File"
                        },
                    "img": {
                        "nome_file": getattr(obj.img, 'name', "None File") if obj.img else "None File",
                        "path_file": getattr(obj.img, 'path', "None File") if obj.img else "None File"
                        }
                },
                "testo_soluzione": {
                    "it": solution_text,
                    "eng": eng,
                    "esp": esp,
                    "de": de,
                    "fr": fr,
                    "dk": dk,
                    "pt": pt,
                    "ru": ru,
                    "pl": pl,
                    "no": no,
                    "se": se
                }
            }
            
            # ...and pushing 
            self.JM.write_alarm_json(alarm_file)
            
            logger_view(obj.titolo, "Creato allarme")
        except Exception as e:
            #print(f"Nooooooooooooo: {e}")
            logger_view(e, "Catturata eccezzione try-except inserimento allarme nel JSON")
            
        messages.success(request, "Allarme creato correttamente")
    #
    def update_alarm(self, request: HttpRequest, search_title, title, solution_text, img, video, chk_dict: dict, alarm_list):
        
        # IN ANY CASE YOU WANT THE USER TO UPDATE THE ALARMS WITH THE SEARCH-TITLE BAR JUST CHANGE 'alarm_list_value' WITH 'search_title'
        
        # read the file
        with open(self.JSON_PATH) as file:
            alarm_json_file = json.load(file)
        
        if not alarm_list:
            messages.warning(request, "Nessun allarme selezionato")
            return
        
        updated = False
        
        # alarm_title
        alarm_list_value = alarm_list[0]
        
        try:
            # check only the inserted in the DB - not  the JSON
            with transaction.atomic():
                
                # qs = AllarmiSoluzioni.objects.filter(titolo=alarm_list_value)
                qs = AllarmiSoluzioni.objects.get(titolo=alarm_list_value)
        
                # if qs.exists() -> in case of .filter()
                try:
                    qs = AllarmiSoluzioni.objects.get(titolo=alarm_list_value)
                except AllarmiSoluzioni.DoesNotExist:
                    messages.info(request, "L'allarme selezionato non esiste nel DB")
                    return
                
                # fields_to_update = {}
                
                # CHECK TITLE - OK
                if chk_dict.get("alarm") and title:
                    # fields_to_update["titolo"] = title
                    qs.titolo = title
                    alarm_json_file["lista_allarmi"][alarm_list_value] = title
                    
                    updated = True
                #
                # CHECK SOLUTION - OK
                if chk_dict.get("solution") and solution_text:
                    
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
                    
                    logger_view(alarm_list_value, "Titolo Allarme")
                    
                    alarm_json_file["lista_allarmi"][alarm_list_value]["testo_soluzione"] = {
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
                    
                    try:
                        qs.text_it = solution_text
                        qs.text_eng = trans_eng
                        qs.text_esp = trans_esp
                        qs.text_de = trans_de
                        qs.text_fr = trans_fr
                        qs.text_dk = trans_dk
                        qs.text_pt = trans_pt
                        qs.text_ru = trans_ru
                        qs.text_pl = trans_pl
                        qs.text_no = trans_no
                        qs.text_se = trans_se
                        
                        '''
                        in case of .filter()
                        fields_to_update["text_it"] = solution_text
                        fields_to_update["text_eng"]=trans_eng
                        fields_to_update["text_esp"]=trans_esp
                        fields_to_update["text_de"]=trans_de
                        fields_to_update["text_fr"]=trans_fr
                        fields_to_update["text_dk"]=trans_dk
                        fields_to_update["text_pt"]=trans_pt
                        fields_to_update["text_ru"]=trans_ru
                        fields_to_update["text_pl"]=trans_pl
                        fields_to_update["text_no"]=trans_no
                        fields_to_update["text_se"]=trans_se
                        '''
                        updated = True
                        
                        # fields_to_update.update({f"text_{k}": v for k, v in translations.items()})
                    except Exception as e:
                        messages.warning(request, f"Errore traduzione automatica: [{e}]")

                # CHECK IMG - OK
                if chk_dict.get("img") and img:
                    # fields_to_update["img"] = img
                    qs.img = img
                    alarm_json_file["lista_allarmi"][alarm_list_value]["media"]["img"] = {
                        "nome_file": img if img else "None File",
                        "path_file": img if img else "None File"
                    }
                    
                    updated = True
                #
                # CHECK VIDEO - OK
                if chk_dict.get("video") and video:
                    # fields_to_update["video"] = video
                    qs.video = video
                    alarm_json_file["lista_allarmi"][alarm_list_value]["media"]["video"] = {
                        "nome_file": video if qs.video else "None File",
                        "path_file": video if qs.video else "None File"
                    }
                    updated = True
        except Exception as e:
            messages.error(request, f"Errore durante update: {e}")
        #
        if updated:
            
            qs.save()
            
            with open(self.JSON_PATH,'w+') as file:
                alarm_json_file = json.dump(alarm_json_file, file, indent=4)
                
            messages.success(request, "Allarme aggiornato correttamente")
        else:
            messages.info(request, "Nessun campo aggiornato")
        
        '''
        # Execute update only if there are fields to update
        if fields_to_update:
            qs.update(**fields_to_update)
            messages.success(request, "Allarme aggiornato correttamente")
        else:
            messages.info(request, "Nessun campo selezionato o fornito da aggiornare")
        '''
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
    # 
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
            
            logger_view(request.build_absolute_uri(alarm.img.url), "Percorso dell'immagine  dopo aver premuto Download nel url /manual-admin/")
            
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
#