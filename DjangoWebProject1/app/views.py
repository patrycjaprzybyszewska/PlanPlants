# -*- coding: utf-8 -*-
from datetime import datetime
from django.db import connection
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import Kolekcja, Roslina, Gleba, Nawoz, Rodzaj, WarunkiHodowli, Relacja
from .forms import (
    KolekcjaForm, RoslinaForm, GlebaForm, NawozForm,
    RodzajForm, WarunkiHodowliForm, RelacjaForm
)


def _zarejestruj_podprogramy():
    """
    Rejestruje podprogramy składowane (funkcje) w bazie SQLite.
    """
    connection.ensure_connection()
    conn = connection.connection

    if conn is None:
        return

  
    def sprawdz_kwitnienie(okres_kwitnienia, miesiac):
        try:
            if not okres_kwitnienia or not miesiac:
                return 'Kwiat: Brak danych'
            czesci = okres_kwitnienia.strip().split('-')
            if len(czesci) != 2:
                return 'Kwiat: Blad formatu'
            m_start = int(czesci[0])
            m_end = int(czesci[1])
            if m_start <= int(miesiac) <= m_end:
                return 'Kwiat: OK'
            return 'Kwiat: NIE'
        except Exception:
            return 'Kwiat: Blad danych'


    def sprawdz_temperature(temperatura, temp_min, temp_maks):
        try:
            if temperatura is None:
                return 'Temp: Brak danych'
            t = float(temperatura)
            t_min = float(temp_min) if temp_min is not None else -999.0
            t_max = float(temp_maks) if temp_maks is not None else 999.0
            if t < t_min:
                return 'ALERT: Zbyt zimno'
            elif t > t_max:
                return 'ALERT: Zbyt goraco'
            return 'Temp: OK'
        except Exception:
            return 'Temp: Blad formatu'

    try:
        conn.create_function('sprawdz_kwitnienie', 2, sprawdz_kwitnienie)
        conn.create_function('sprawdz_temperature', 3, sprawdz_temperature)
    except Exception:
        pass


def home(request):
    gatunki = []
    ilosci = []
    statusy = []
    alerty_allelopatii = []
    alerty_warunkow = []

    aktualny_widok = request.GET.get('widok', 'tabela')


    try:
        _zarejestruj_podprogramy()
        dane_wykresu = Roslina.objects.values('gatunek').annotate(ilosc=Count('id_rosliny'))
        gatunki = [item['gatunek'] for item in dane_wykresu]
        ilosci = [item['ilosc'] for item in dane_wykresu]
    except Exception as e:
        print("Błąd inicjalizacji wykresu:", str(e))


    try:
        kolekcje_queryset = Kolekcja.objects.annotate(suma_roslin=Count('rosliny'))
    except Exception as e:
        print("Nie można pobrać kolekcji:", str(e))
        kolekcje_queryset = []

    for kol in kolekcje_queryset:
        status_kwitnienia = 'Brak danych'
        status_temperatury = 'Brak analizy temp.'
        lista_gleb = 'Brak danych'
        lista_nawozow = 'Brak nawozu'
        
        try:
            pierwsza_roslina = Roslina.objects.filter(id_kolekcji=kol).first()
            
            if pierwsza_roslina:
                miesiac_posadzenia = str(kol.data_posadzenia.month) if kol.data_posadzenia else str(datetime.now().month)
                okres = str(pierwsza_roslina.okres_kwitnienia) if pierwsza_roslina.okres_kwitnienia else ""

 
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(f"SELECT sprawdz_kwitnienie('{okres}', '{miesiac_posadzenia}')")
                        res = cursor.fetchone()
                        if res: status_kwitnienia = res[0]
                except Exception as e:
                    status_kwitnienia = f"Błąd Kwiat: {str(e)[:15]}"
                
                rodzaj = pierwsza_roslina.id_rodzaju
                warunki = rodzaj.id_warunku if rodzaj else None
                
                if warunki:
                    temp_kolekcji = str(kol.temperatura) if kol.temperatura is not None else "0"
                    t_min = str(warunki.temp_min) if warunki.temp_min is not None else "0"
                    t_max = str(warunki.temp_maks) if warunki.temp_maks is not None else "0"

                    
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute(f"SELECT sprawdz_temperature('{temp_kolekcji}', '{t_min}', '{t_max}')")
                            res = cursor.fetchone()
                            if res: status_temperatury = res[0]
                    except Exception as e:
                        status_temperatury = f"Błąd Temp: {str(e)[:15]}"
                    
                   
                    try:
                       
                        gleba_obj = Gleba.objects.filter(id_warunku=warunki).first()
                        if gleba_obj:
                          
                            lista_gleb = getattr(gleba_obj, 'nazwa', getattr(gleba_obj, 'typ', 'Zapisana gleba'))
                            
                          
                            nawoz_obj = None
                      
                            if not nawoz_obj:
                                try: nawoz_obj = Nawoz.objects.filter(id_gleby=gleba_obj).first()
                                except Exception: pass
                        
                            if not nawoz_obj:
                                try: nawoz_obj = Nawoz.objects.filter(gleba=gleba_obj).first()
                                except Exception: pass
                                
                         
                            if not nawoz_obj:
                                try: nawoz_obj = Nawoz.objects.filter(id_gleba=gleba_obj).first()
                                except Exception: pass

                           
                            if not nawoz_obj:
                                try: nawoz_obj = getattr(gleba_obj, 'nawoz', getattr(gleba_obj, 'id_nawozu', None))
                                except Exception: pass

                         
                            if nawoz_obj:
                                lista_nawozow = getattr(nawoz_obj, 'nazwa', getattr(nawoz_obj, 'producent', 'Zapisany nawóz'))
                    except Exception as e:
                        lista_gleb = f"Błąd danych: {str(e)[:15]}"

        except Exception as e:
            status_kwitnienia = "Błąd wiersza"

        statusy.append((
            kol.nazwa_kolekcji,
            status_kwitnienia,
            status_temperatury,
            kol.suma_roslin,
            lista_gleb,
            lista_nawozow
        ))
        
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT 
                    k.nazwa_kolekcji,
                    r1.nazwa_powszechna || ' (' || r1.gatunek || ')' AS roslina1,
                    r2.nazwa_powszechna || ' (' || r2.gatunek || ')' AS roslina2
                FROM app_relacja rel
                JOIN app_roslina r1 ON rel.id_rosliny_1_id = r1.id_rosliny
                JOIN app_roslina r2 ON rel.id_rosliny_2_id = r2.id_rosliny
                JOIN app_kolekcja k ON r1.id_kolekcji_id = k.id_kolekcji
                WHERE r1.id_kolekcji_id = r2.id_kolekcji_id AND rel.typ_relacji = 'Allelopatia ujemna'
            """)
            alerty_allelopatii = cursor.fetchall()
    except Exception:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT k.nazwa_kolekcji, r1.nazwa_powszechna, r2.nazwa_powszechna
                    FROM relacja rel
                    JOIN roslina r1 ON rel.id_rosliny_1 = r1.id_rosliny
                    JOIN roslina r2 ON rel.id_rosliny_2 = r2.id_rosliny
                    JOIN kolekcja k ON r1.id_kolekcji = k.id_kolekcji
                    WHERE r1.id_kolekcji = r2.id_kolekcji AND rel.typ_relacji = 'Allelopatia ujemna'
                """)
                alerty_allelopatii = cursor.fetchall()
        except Exception:
            pass


    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    k.nazwa_kolekcji,
                    r.nazwa_powszechna || ' (' || r.gatunek || ')' AS nazwa_rosliny,
                    k.temperatura AS temp_kolekcji,
                    w.temp_min,
                    w.temp_maks
                FROM app_kolekcja k
                JOIN app_roslina r ON k.id_kolekcji = r.id_kolekcji_id
                JOIN app_rodzaj ro ON r.id_rodzaju_id = ro.id_rodzaju
                JOIN app_warunki_hodowli w ON ro.id_warunku_id = w.id_warunku
                WHERE k.temperatura < w.temp_min OR k.temperatura > w.temp_maks
            """)
            alerty_warunkow = cursor.fetchall()
    except Exception:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT k.nazwa_kolekcji, r.nazwa_powszechna, k.temperatura, w.temp_min, w.temp_maks
                    FROM kolekcja k
                    JOIN roslina r ON k.id_kolekcji = r.id_kolekcji
                    JOIN rodzaj ro ON r.id_rodzaju = ro.id_rodzaju
                    JOIN warunki_hodowli w ON ro.id_warunku = w.id_warunku
                    WHERE k.temperatura < w.temp_min OR k.temperatura > w.temp_maks
                """)
                alerty_warunkow = cursor.fetchall()
        except Exception:
            pass

    return render(request, 'app/index.html', {
        'title': 'Strona Glowna',
        'year': datetime.now().year,
        'gatunki': gatunki,
        'ilosci': ilosci,
        'statusy': statusy,
        'alerty_allelopatii': alerty_allelopatii,
        'alerty_warunkow': alerty_warunkow,  
        'aktualny_widok': aktualny_widok,
    })

def moje_kolekcje(request):
    if request.method == 'POST':
        form = KolekcjaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kolekcja zostala dodana.')
            return redirect('moje_kolekcje')
    else:
        form = KolekcjaForm()

    _zarejestruj_podprogramy()
    statusy_temp = {}
    
    try:
        with connection.cursor() as cursor:
            try:
                cursor.execute("""
                    SELECT 
                        k.id_kolekcji,
                        k.nazwa_kolekcji,
                        sprawdz_temperature(k.temperatura, w.temp_min, w.temp_maks) AS status_temp
                    FROM app_kolekcja k
                    LEFT JOIN app_roslina r ON k.id_kolekcji = r.id_kolekcji_id
                    LEFT JOIN app_rodzaj ro ON r.id_rodzaju_id = ro.id_rodzaju
                    LEFT JOIN app_warunki_hodowli w ON ro.id_warunku_id = w.id_warunku
                    GROUP BY k.id_kolekcji
                """)
                rows = cursor.fetchall()
            except Exception:
                cursor.execute("""
                    SELECT 
                        k.id_kolekcji,
                        k.nazwa_kolekcji,
                        sprawdz_temperature(k.temperatura, w.temp_min, w.temp_maks) AS status_temp
                    FROM kolekcja k
                    LEFT JOIN roslina r ON k.id_kolekcji = r.id_kolekcji
                    LEFT JOIN rodzaj ro ON r.id_rodzaju = ro.id_rodzaju
                    LEFT JOIN warunki_hodowli w ON ro.id_warunku = w.id_warunku
                    GROUP BY k.id_kolekcji
                """)
                rows = cursor.fetchall()

            for row in rows:
                statusy_temp[row[0]] = row[2]
    except Exception as e:
        print("Błąd pobierania temperatur w moje_kolekcje:", str(e))

    return render(request, 'app/moje_kolekcje.html', {
        'kolekcje': Kolekcja.objects.prefetch_related('rosliny').all().order_by('-data_posadzenia'),
        'form': form,
        'title': 'Moje Kolekcje',
        'statusy_temp': statusy_temp,  
    })


def moje_rosliny(request):
    query = request.GET.get('q', '').strip()
    rosliny_list = Roslina.objects.select_related(
        'id_kolekcji', 'id_rodzaju', 'id_rodzaju__id_warunku'
    ).all()

    if query:
        rosliny_list = rosliny_list.filter(nazwa_powszechna__icontains=query) | \
                       rosliny_list.filter(gatunek__icontains=query)

    if request.method == 'POST':
        form = RoslinaForm(request.POST)
        form_relacja = RelacjaForm(request.POST)

        if form.is_valid():
            nowa_roslina = form.save()

            typ_relacji = request.POST.get('typ_relacji')
            id_rosliny_2 = request.POST.get('id_rosliny_2')

            if typ_relacji and id_rosliny_2:
                try:
                    druga_roslina = Roslina.objects.get(pk=id_rosliny_2)
                    Relacja.objects.create(
                        typ_relacji=typ_relacji,
                        id_rosliny_1=nowa_roslina,
                        id_rosliny_2=druga_roslina
                    )
                    messages.success(request, 'Roslina oraz relacja zostaly dodane.')
                except Exception:
                    messages.warning(request, 'Roslina dodana, ale blad przy tworzeniu relacji.')
            else:
                messages.success(request, 'Roslina zostala dodana.')

            return redirect('moje_rosliny')
    else:
        form = RoslinaForm()
        form_relacja = RelacjaForm()

    return render(request, 'app/moje_rosliny.html', {
        'rosliny': rosliny_list,
        'form': form,
        'form_relacja': form_relacja,
        'title': 'Moje Rosliny',
        'query': query,
    })


def szukaj_rosliny(request):
    query = request.GET.get('q', '').strip()
    wyniki = []

    if query:
        _zarejestruj_podprogramy()

        rosliny = Roslina.objects.select_related('id_rodzaju', 'id_rodzaju__id_warunku').filter(
            nazwa_powszechna__icontains=query
        ) | Roslina.objects.select_related('id_rodzaju', 'id_rodzaju__id_warunku').filter(
            gatunek__icontains=query
        )

        for roslina in rosliny:
            warunki = roslina.get_warunki()
            gleba = roslina.get_gleba()
            nawozy = list(gleba.nawozy.all()) if gleba else []

            status_kwitnienia = 'Kwiat: Brak danych'
            try:
                okres_val = str(roslina.okres_kwitnienia) if roslina.okres_kwitnienia else ""
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"SELECT sprawdz_kwitnienie('{okres_val}', CAST(strftime('%m', 'now') AS INTEGER))"
                    )
                    status_kwitnienia = cursor.fetchone()[0]
            except Exception:
                pass

            status_temperatury = 'Temp: Brak danych'
            if warunki:
                try:
                    kolekcja = roslina.id_kolekcji
                    temp = str(kolekcja.temperatura) if kolekcja and kolekcja.temperatura else "0"
                    t_min = str(warunki.temp_min) if warunki.temp_min is not None else "0"
                    t_max = str(warunki.temp_maks) if warunki.temp_maks is not None else "0"
                    
                    with connection.cursor() as cursor:
                        cursor.execute(f"SELECT sprawdz_temperature('{temp}', '{t_min}', '{t_max}')")
                        status_temperatury = cursor.fetchone()[0]
                except Exception:
                    pass

            wyniki.append({
                'roslina': roslina,
                'warunki': warunki,
                'gleba': gleba,
                'nawozy': nawozy,
                'status_kwitnienia': status_kwitnienia,
                'status_temperatury': status_temperatury,
            })

    return render(request, 'app/szukaj.html', {
        'title': 'Szukaj rosliny',
        'query': query,
        'wyniki': wyniki,
        'year': datetime.now().year,
    })


def pielegnacja(request):
    form_gleba = GlebaForm()
    form_nawoz = NawozForm()
    form_warunki = WarunkiHodowliForm()

    if request.method == 'POST':
        if 'akcja_gleba' in request.POST:
            form_gleba = GlebaForm(request.POST)
            if form_gleba.is_valid():
                form_gleba.save()
                messages.success(request, 'Gleba zostala dodana.')
                return redirect('pielegnacja')

        elif 'akcja_nawoz' in request.POST:
            form_nawoz = NawozForm(request.POST)
            if form_nawoz.is_valid():
                form_nawoz.save()
                messages.success(request, 'Nawoz zostal dodany.')
                return redirect('pielegnacja')

        elif 'akcja_warunki' in request.POST:
            form_warunki = WarunkiHodowliForm(request.POST)
            if form_warunki.is_valid():
                form_warunki.save()
                messages.success(request, 'Warunki hodowli zostaly dodane.')
                return redirect('pielegnacja')

    return render(request, 'app/pielegnacja.html', {
       'gleby': Gleba.objects.select_related('id_warunku').all().order_by('typ'),
       'nawozy_z_glebami': Nawoz.objects.select_related('id_gleby').all().order_by('producent'),
        'warunki': WarunkiHodowli.objects.prefetch_related('gleby').all(),
        'form_gleba': form_gleba,
        'form_nawoz': form_nawoz,
        'form_warunki': form_warunki,
        'title': 'Warunki i Pielegnacja'
    })


def relacje(request):
    if request.method == 'POST':
        form = RelacjaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Relacja zostala dodana.')
            return redirect('relacje')
        else:
            messages.error(request, 'Nie udalo sie dodac relacji. Sprawdz dane.')
    else:
        form = RelacjaForm()

    return render(request, 'app/relacje.html', {
        'relacje': Relacja.objects.select_related('id_rosliny_1', 'id_rosliny_2').all(),
        'form': form,
        'title': 'Relacje miedzy roslinami',
    })


def usun_relacje(request, id_relacji):
    get_object_or_404(Relacja, pk=id_relacji).delete()
    return redirect('relacje')


def usun_kolekcje(request, id_kolekcji):
    get_object_or_404(Kolekcja, pk=id_kolekcji).delete()
    return redirect('moje_kolekcje')


def usun_glebe(request, id_gleby):
    get_object_or_404(Gleba, pk=id_gleby).delete()
    return redirect('pielegnacja')


def usun_nawoz(request, id_nawozu):
    get_object_or_404(Nawoz, pk=id_nawozu).delete()
    return redirect('pielegnacja')


def usun_rosline(request, id_rosliny):
    get_object_or_404(Roslina, pk=id_rosliny).delete()
    return redirect('moje_rosliny')


def rodzaje(request):
    if request.method == 'POST':
        form = RodzajForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rodzaj zostal dodany.')
            return redirect('rodzaje')
    else:
        form = RodzajForm()

    return render(request, 'app/rodzaje.html', {
        'rodzaje': Rodzaj.objects.select_related('id_warunku').all().order_by('rodzaj'),
        'form': form,
        'title': 'Rodzaje Roslin'
    })


def usun_rodzaj(request, id_rodzaju):
    get_object_or_404(Rodzaj, pk=id_rodzaju).delete()
    return redirect('rodzaje')


def edytuj_rosline(request, id_rosliny):
    roslina = get_object_or_404(Roslina, pk=id_rosliny)
    if request.method == 'POST':
        form = RoslinaForm(request.POST, instance=roslina)
        if form.is_valid():
            form.save()
            messages.success(request, 'Roslina zostala zaktualizowana.')
        else:
            messages.error(request, 'Blad podczas aktualizacji rosliny.')
    return redirect('moje_rosliny')


def edytuj_kolekcje(request, id_kolekcji):
    kolekcja = get_object_or_404(Kolekcja, pk=id_kolekcji)
    if request.method == 'POST':
        form = KolekcjaForm(request.POST, instance=kolekcja)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kolekcja zostala zaktualizowana.')
        else:
            messages.error(request, 'Blad podczas aktualizacji kolekcji.')
    return redirect('moje_kolekcje')


def usun_warunki(request, id_warunku):
    get_object_or_404(WarunkiHodowli, pk=id_warunku).delete()
    return redirect('pielegnacja')