from django import forms


# login form (log btn, insert values) -- general log-in form
class Loginform(forms.Form):
    username = forms.CharField(max_length=64)
    password = forms.CharField(widget=forms.PasswordInput)
