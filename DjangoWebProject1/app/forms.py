# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import Gleba, Nawoz, Roslina, WarunkiHodowli, Kolekcja, Rodzaj, Relacja

class BootstrapAuthenticationForm(AuthenticationForm):
    username = forms.CharField(max_length=254, widget=forms.TextInput({'class': 'form-control', 'placeholder': 'User name'}))
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput({'class': 'form-control', 'placeholder': 'Password'}))

class KolekcjaForm(forms.ModelForm):
    class Meta:
        model = Kolekcja
        fields = ['nazwa_kolekcji', 'data_posadzenia', 'status', 'temperatura', 'id_warunku']
        widgets = {
            'nazwa_kolekcji': forms.TextInput(attrs={'class': 'form-control'}),
            'data_posadzenia': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.TextInput(attrs={'class': 'form-control'}),
            'temperatura': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'np. 20.5', 'step': '0.1'}),
            'id_warunku': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'nazwa_kolekcji': 'Nazwa kolekcji',
            'data_posadzenia': 'Data posadzenia',
            'status': 'Status',
            'temperatura': 'Temperatura (C)',
            'id_warunku': 'Powiazane warunki hodowli',
        }

class RoslinaForm(forms.ModelForm):
    class Meta:
        model = Roslina
        fields = ['gatunek', 'nazwa_powszechna', 'opis', 'okres_kwitnienia', 'id_rodzaju', 'id_kolekcji']
        widgets = {
            'gatunek': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Np. Rosa canina'}),
            'nazwa_powszechna': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Np. Roza dzika'}),
            'opis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Krotki opis rosliny...'}),
            'okres_kwitnienia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Np. 05-07'}),
            'id_rodzaju': forms.Select(attrs={'class': 'form-control'}),
            'id_kolekcji': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'gatunek': 'Gatunek (Nazwa lacinska)',
            'nazwa_powszechna': 'Nazwa powszechna',
            'opis': 'Opis rosliny',
            'okres_kwitnienia': 'Okres kwitnienia (MM-MM)',
            'id_rodzaju': 'Rodzaj rosliny',
            'id_kolekcji': 'Kolekcja',
        }

class GlebaForm(forms.ModelForm):
    class Meta:
        model = Gleba
        fields = ['nazwa', 'typ', 'ph_gleby', 'id_warunku']
        widgets = {
            'nazwa': forms.TextInput(attrs={'class': 'form-control'}),
            'typ': forms.TextInput(attrs={'class': 'form-control'}),
            'ph_gleby': forms.TextInput(attrs={'class': 'form-control'}),
            'id_warunku': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'nazwa': 'Nazwa podloza',
            'typ': 'Typ gleby',
            'ph_gleby': 'Odczyn pH',
            'id_warunku': 'Wymagana w warunkach',
        }

class NawozForm(forms.ModelForm):
    class Meta:
        model = Nawoz
        fields = ['producent', 'zawartosc_azotu', 'zawartosc_fosforu', 'id_gleby']
        widgets = {
            'producent': forms.TextInput(attrs={'class': 'form-control'}),
            'zawartosc_azotu': forms.TextInput(attrs={'class': 'form-control'}),
            'zawartosc_fosforu': forms.TextInput(attrs={'class': 'form-control'}),
            'id_gleby': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'producent': 'Producent nawozu',
            'zawartosc_azotu': 'Zawartosc azotu (N)',
            'zawartosc_fosforu': 'Zawartosc fosforu (P)',
            'id_gleby': 'Przeznaczony do gleby',
        }

class RodzajForm(forms.ModelForm):
    class Meta:
        model = Rodzaj
        fields = ['rodzaj', 'id_warunku']
        labels = {
            'rodzaj': 'Nazwa rodzaju',
            'id_warunku': 'Warunki hodowli',
        }
        widgets = {
            'rodzaj': forms.TextInput(attrs={'class': 'form-control'}),
            'id_warunku': forms.Select(attrs={'class': 'form-control'}),
        }

class WarunkiHodowliForm(forms.ModelForm):
    class Meta:
        model = WarunkiHodowli
        fields = ['wilgotnosc', 'naslonecznienie', 'temp_min', 'temp_maks']
        widgets = {
            'wilgotnosc': forms.TextInput(attrs={'class': 'form-control'}),
            'naslonecznienie': forms.TextInput(attrs={'class': 'form-control'}),
            'temp_min': forms.TextInput(attrs={'class': 'form-control'}),
            'temp_maks': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'wilgotnosc': 'Wilgotnosc',
            'naslonecznienie': 'Naslonecznienie',
            'temp_min': 'Temperatura minimalna (C)',
            'temp_maks': 'Temperatura maksymalna (C)',
        }

class RelacjaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(RelacjaForm, self).__init__(*args, **kwargs)
  
        self.fields['typ_relacji'].required = False
        self.fields['id_rosliny_2'].required = False
        self.fields['id_rosliny_1'].required = False
        
        self.fields['typ_relacji'].choices = [('', '--- Brak relacji (opcjonalnie) ---')] + list(self.fields['typ_relacji'].choices)[1:]
        self.fields['id_rosliny_2'].choices = [('', '--- Wybierz druga rosline ---')] + list(self.fields['id_rosliny_2'].choices)[1:]

    class Meta:
        model = Relacja
        fields = ['typ_relacji', 'id_rosliny_1', 'id_rosliny_2']
        widgets = {
            'typ_relacji': forms.Select(attrs={'class': 'form-control'}),
            'id_rosliny_1': forms.Select(attrs={'class': 'form-control'}),
            'id_rosliny_2': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'typ_relacji': 'Typ relacji',
            'id_rosliny_1': 'Roslina 1',
            'id_rosliny_2': 'Wybierz rosline do pary',
        }