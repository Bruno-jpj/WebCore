from django import forms
from .models import LanguageModel

# login form (log btn, insert values) -- general log-in form
class Loginform(forms.Form):
    username = forms.CharField(max_length=64)
    password = forms.CharField(widget=forms.PasswordInput)

class ChoseLanguage(forms.ModelForm):
    class Meta:
        model = LanguageModel
        fields = [
            'language'
        ]
