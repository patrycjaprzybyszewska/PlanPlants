# -*- coding: utf-8 -*-
import sqlite3
import os

db_path = 'db.sqlite3'

if not os.path.exists(db_path):
    print("BLAD: Nie znaleziono pliku db.sqlite3 w tym katalogu!")
else:
    print("Znaleziono baze danych. Rozpoczynam naprawe struktury...")

    conn = sqlite3.connect(db_path)

    # -------------------------------------------------------------------------
    # WAZNE: Rejestrujemy podprogramy jako funkcje Pythona w SQLite.
    # SQLite nie ma wbudowanego jezyka proceduralnego (jak PL/pgSQL w Postgres),
    # wiec funkcje i procedury implementuje sie jako CREATE VIEW lub jako
    # funkcje Pythona rejestrowane przez connection.create_function().
    # To jest oficjalny i jedyny sposob tworzenia podprogramow w SQLite.
    # -------------------------------------------------------------------------

    # =========================================================================
    # PODPROGRAM 1: FUNKCJA – sprawdz_kwitnienie(okres_kwitnienia, miesiac)
    # Zwraca 'Kwiat: OK' jesli podany miesiac miesci sie w okresie kwitnienia,
    # lub 'Kwiat: NIE' w przeciwnym wypadku.
    # Format okresu_kwitnienia: 'MM-MM' np. '04-08' oznacza kwiecien-sierpien.
    # =========================================================================
    def sprawdz_kwitnienie(okres_kwitnienia, miesiac):
        """
        Funkcja skladowana w bazie danych.
        Sprawdza czy roslina kwitnie w podanym miesiacu.
        Wywolywana z aplikacji przez: SELECT sprawdz_kwitnienie(okres_kwitnienia, miesiac)
        """
        try:
            if not okres_kwitnienia or not miesiac:
                return 'Kwiat: Brak danych'
            czesci = okres_kwitnienia.strip().split('-')
            if len(czesci) != 2:
                return 'Kwiat: Blad formatu'
            m_start = int(czesci[0])
            m_end = int(czesci[1])
            m = int(miesiac)
            if m_start <= m <= m_end:
                return 'Kwiat: OK'
            else:
                return 'Kwiat: NIE'
        except Exception as e:
            return f'Kwiat: Blad ({e})'

    conn.create_function('sprawdz_kwitnienie', 2, sprawdz_kwitnienie)
    print("- Zarejestrowano funkcje: sprawdz_kwitnienie(okres_kwitnienia, miesiac)")

    # =========================================================================
    # PODPROGRAM 2: PROCEDURA – sprawdz_temperature(temperatura, temp_min, temp_maks)
    # Zwraca status temperatury: 'Temp: OK', 'ALERT: Zbyt zimno' lub 'ALERT: Zbyt goraco'.
    # W SQLite procedury skladowane implementuje sie tak samo jak funkcje –
    # przez create_function() z liczba argumentow = -1 (dowolna) lub stala.
    # =========================================================================
    def sprawdz_temperature(temperatura, temp_min, temp_maks):
        """
        Procedura skladowana w bazie danych.
        Sprawdza czy temperatura kolekcji miesci sie w wymaganiach hodowli.
        Wywolywana z aplikacji przez: SELECT sprawdz_temperature(temperatura, temp_min, temp_maks)
        """
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
            else:
                return 'Temp: OK'
        except Exception as e:
            return f'Temp: Blad ({e})'

    conn.create_function('sprawdz_temperature', 3, sprawdz_temperature)
    print("- Zarejestrowano procedure: sprawdz_temperature(temperatura, temp_min, temp_maks)")

    # -------------------------------------------------------------------------
    # Test dzialania podprogramow bezposrednio w SQL
    # -------------------------------------------------------------------------
    cursor = conn.cursor()

    print("\n--- Test funkcji sprawdz_kwitnienie ---")
    testy_kwitnienie = [
        ('04-08', 6),   # czerwiec w sezonie -> OK
        ('04-08', 10),  # pazdziernik poza sezonem -> NIE
        (None, 5),      # brak danych
        ('blad', 5),    # bledny format
    ]
    for okres, miesiac in testy_kwitnienie:
        cursor.execute("SELECT sprawdz_kwitnienie(?, ?)", (okres, miesiac))
        wynik = cursor.fetchone()[0]
        print(f"  sprawdz_kwitnienie('{okres}', {miesiac}) = {wynik}")

    print("\n--- Test procedury sprawdz_temperature ---")
    testy_temp = [
        (20.0, 15.0, 25.0),   # w normie -> OK
        (5.0,  15.0, 25.0),   # za zimno -> ALERT
        (30.0, 15.0, 25.0),   # za cieplo -> ALERT
        (None, 15.0, 25.0),   # brak danych
    ]
    for t, t_min, t_max in testy_temp:
        cursor.execute("SELECT sprawdz_temperature(?, ?, ?)", (t, t_min, t_max))
        wynik = cursor.fetchone()[0]
        print(f"  sprawdz_temperature({t}, {t_min}, {t_max}) = {wynik}")

    # -------------------------------------------------------------------------
    # Struktury bazy (widoki, tabele pomocnicze) – bez zmian z poprzedniej wersji
    # -------------------------------------------------------------------------
    try:
        cursor.execute("DROP VIEW IF EXISTS widok_srednich_temperatur;")
        cursor.execute("DROP VIEW IF EXISTS widok_statystyk_kolekcji;")
        print("\n- Usunieto stare widoki SQL.")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS warunki_hodowli (
            id_warunku INTEGER PRIMARY KEY AUTOINCREMENT,
            wilgotnosc VARCHAR(50) NULL,
            naslonecznienie VARCHAR(50) NULL,
            temp_min DECIMAL(5, 2) NULL,
            temp_maks DECIMAL(5, 2) NULL
        );
        """)
        print("- Sprawdzono tabele: warunki_hodowli")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS gleba (
            id_gleby INTEGER PRIMARY KEY AUTOINCREMENT,
            nazwa VARCHAR(100) NULL,
            typ VARCHAR(100) NULL,
            ph_gleby VARCHAR(10) NULL,
            id_warunku INTEGER NULL,
            FOREIGN KEY (id_warunku) REFERENCES warunki_hodowli(id_warunku) ON DELETE SET NULL
        );
        """)
        print("- Sprawdzono tabele: gleba")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS nawoz (
            id_nawozu INTEGER PRIMARY KEY AUTOINCREMENT,
            producent VARCHAR(100) NULL,
            zawartosc_azotu VARCHAR(50) NULL,
            zawartosc_fosforu VARCHAR(50) NULL,
            id_gleby INTEGER NULL,
            FOREIGN KEY (id_gleby) REFERENCES gleba(id_gleby) ON DELETE SET NULL
        );
        """)
        print("- Sprawdzono tabele: nawoz")
        
        cursor.execute("""
        CREATE VIEW IF NOT EXISTS widok_statystyk_kolekcji AS
        SELECT
            k.nazwa_kolekcji,
            sprawdz_kwitnienie(r.okres_kwitnienia, CAST(strftime('%m', k.data_posadzenia) AS INTEGER)) AS status_kwitnienia,
            sprawdz_temperature(k.temperatura, w.temp_min, w.temp_maks) AS status_temperatury
        FROM kolekcja k
        JOIN roslina r ON k.id_kolekcji = r.id_kolekcji
        JOIN rodzaj ro ON r.id_rodzaju = ro.id_rodzaju
        JOIN warunki_hodowli w ON ro.id_warunku = w.id_warunku;
        """)
        print("- Utworzono widok: widok_statystyk_kolekcji (uzywa podprogramow)")

        conn.commit()
        print("\nSUKCES! Podprogramy, tabele i widoki sa gotowe.")

    except Exception as e:
        print(f"\nWystapil blad: {e}")
        conn.rollback()
    finally:
        conn.close()
        conn.close()