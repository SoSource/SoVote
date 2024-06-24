from django import forms
# from django.contrib.auth import (
#     authenticate,
#     get_user_model,
#     login,
#     logout,
#     )
from .models import Agenda, Post

from datetime import date

today = date.today()
    
class AgendaForm(forms.ModelForm):
    date = forms.DateField(widget=forms.TextInput(attrs={'value': today, 'type': 'date'}), required=True)

    class Meta:
        model = Agenda
        fields = ['date']

class SearchForm(forms.ModelForm):
    # date = forms.DateField(widget=forms.TextInput(attrs={'value': today, 'type': 'date'}), required=True)

    class Meta:
        model = Post
        fields = ['pointerType']
