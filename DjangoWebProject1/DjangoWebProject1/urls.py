from datetime import datetime
from django.urls import path
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView

from app import views
from app import forms

urlpatterns = [
    path('', views.home, name='home'),
   # path('about/', views.about, name='about'),

    # --- Wyszukiwanie (główna funkcjonalność) ---
    path('szukaj/', views.szukaj_rosliny, name='szukaj_rosliny'),

    # --- Rośliny ---
    path('rosliny/', views.moje_rosliny, name='moje_rosliny'),
    # FIX: dodano brakujący URL dla edycji rośliny
    path('rosliny/edytuj/<int:id_rosliny>/', views.edytuj_rosline, name='edytuj_rosline'),
    path('rosliny/usun/<int:id_rosliny>/', views.usun_rosline, name='usun_rosline'),

    # --- Kolekcje ---
    path('kolekcje/', views.moje_kolekcje, name='moje_kolekcje'),
    path('kolekcje/edytuj/<int:id_kolekcji>/', views.edytuj_kolekcje, name='edytuj_kolekcje'),
    path('kolekcje/usun/<int:id_kolekcji>/', views.usun_kolekcje, name='usun_kolekcje'),

    # --- Rodzaje ---
    path('rodzaje/', views.rodzaje, name='rodzaje'),
    path('rodzaje/usun/<int:id_rodzaju>/', views.usun_rodzaj, name='usun_rodzaj'),

    # --- Relacje między roślinami ---
    # FIX: dodano osobny widok dla relacji (zamiast mieszania z formularzem roślin)
    path('relacje/', views.relacje, name='relacje'),
    path('relacje/usun/<int:id_relacji>/', views.usun_relacje, name='usun_relacje'),

    # --- Pielęgnacja (gleba, nawozy, warunki) ---
    path('pielegnacja/', views.pielegnacja, name='pielegnacja'),
    path('pielegnacja/usun-glebe/<int:id_gleby>/', views.usun_glebe, name='usun_glebe'),
    path('pielegnacja/usun-nawoz/<int:id_nawozu>/', views.usun_nawoz, name='usun_nawoz'),
    path('pielegnacja/usun-warunki/<int:id_warunku>/', views.usun_warunki, name='usun_warunki'),

    # --- Auth ---
    path('login/',
         LoginView.as_view(
             template_name='app/login.html',
             authentication_form=forms.BootstrapAuthenticationForm,
             extra_context={
                 'title': 'Log in',
                 'year': datetime.now().year,
             }
         ),
         name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('admin/', admin.site.urls),
]
