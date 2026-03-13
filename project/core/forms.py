from django import forms
from .models import LanguageModel

class ChoseLanguage(forms.ModelForm):
    class Meta:
        model = LanguageModel
        fields = [
            'language'
        ]
    
class SearchAlarmsForm(forms.Form):
    search_text = forms.CharField(max_length=128, required=False, label="Cerca Allarme")

