# -*- coding: utf-8 -*-
from django.db import models

class WarunkiHodowli(models.Model):
    id_warunku = models.AutoField(primary_key=True)
    wilgotnosc = models.CharField(max_length=50, blank=True, null=True)
    naslonecznienie = models.CharField(max_length=50, blank=True, null=True)
    temp_min = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    temp_maks = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'warunki_hodowli'

    def __str__(self):
        return f"Warunki ID {self.id_warunku} (Temp: {self.temp_min}-{self.temp_maks}C)"


class Kolekcja(models.Model):
    id_kolekcji = models.AutoField(primary_key=True)
    nazwa_kolekcji = models.CharField(max_length=100)
    data_posadzenia = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    temperatura = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    id_warunku = models.ForeignKey(WarunkiHodowli, models.DO_NOTHING, db_column='id_warunku', blank=True, null=True)

    class Meta:
        db_table = 'kolekcja'
        indexes = [
            models.Index(fields=['status'], name='idx_kolekcja_status'),
            models.Index(fields=['data_posadzenia'], name='idx_kolekcja_data'),
        ]

    def __str__(self):
        return self.nazwa_kolekcji


class Rodzaj(models.Model):
    id_rodzaju = models.AutoField(primary_key=True)
    rodzaj = models.CharField(max_length=100)
    id_warunku = models.ForeignKey(WarunkiHodowli, models.DO_NOTHING, db_column='id_warunku', blank=True, null=True)

    class Meta:
        db_table = 'rodzaj'
        indexes = [
        
            models.Index(fields=['rodzaj'], name='idx_rodzaj_nazwa'),
        ]

    def __str__(self):
        return self.rodzaj


class Roslina(models.Model):
    id_rosliny = models.AutoField(primary_key=True)
    gatunek = models.CharField(max_length=100, db_index=True)
    nazwa_powszechna = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    opis = models.TextField(blank=True, null=True)
    okres_kwitnienia = models.CharField(max_length=50, blank=True, null=True)
    id_rodzaju = models.ForeignKey(Rodzaj, models.DO_NOTHING, db_column='id_rodzaju', blank=True, null=True, related_name='rosliny')
    id_kolekcji = models.ForeignKey(Kolekcja, models.DO_NOTHING, db_column='id_kolekcji', blank=True, null=True, related_name='rosliny')

    class Meta:
        db_table = 'roslina'
        indexes = [
            models.Index(fields=['gatunek', 'nazwa_powszechna'], name='idx_roslina_gatunek_nazwa'),
            models.Index(fields=['okres_kwitnienia'], name='idx_roslina_kwitnienie'),
            models.Index(fields=['id_kolekcji'], name='idx_roslina_kolekcja'),
        ]

    def __str__(self):
        return self.nazwa_powszechna if self.nazwa_powszechna else self.gatunek

    def get_warunki(self):
        if self.id_rodzaju and self.id_rodzaju.id_warunku:
            return self.id_rodzaju.id_warunku
        return None

    def get_gleba(self):
        warunki = self.get_warunki()
        if warunki:
            return warunki.gleby.first()
        return None


class Gleba(models.Model):
    id_gleby = models.AutoField(primary_key=True)
    nazwa = models.CharField(max_length=100)
    typ = models.CharField(max_length=100, blank=True, null=True)
    ph_gleby = models.CharField(max_length=10, blank=True, null=True)
    id_warunku = models.ForeignKey(WarunkiHodowli, models.DO_NOTHING, db_column='id_warunku', blank=True, null=True, related_name='gleby')

    class Meta:
        db_table = 'gleba'
        indexes = [
            models.Index(fields=['typ'], name='idx_gleba_typ'),
        ]

    def __str__(self):
        return self.nazwa


class Nawoz(models.Model):
    id_nawozu = models.AutoField(primary_key=True)
    producent = models.CharField(max_length=100, blank=True, null=True)
    zawartosc_azotu = models.CharField(max_length=50, blank=True, null=True)
    zawartosc_fosforu = models.CharField(max_length=50, blank=True, null=True)
    id_gleby = models.ForeignKey(Gleba, models.DO_NOTHING, db_column='id_gleby', blank=True, null=True, related_name='nawozy')

    class Meta:
        db_table = 'nawoz'
        indexes = [
     
            models.Index(fields=['producent'], name='idx_nawoz_producent'),
        ]

    def __str__(self):
        return f"{self.producent} (N: {self.zawartosc_azotu}, P: {self.zawartosc_fosforu})"


class Relacja(models.Model):
    CHOICES = [
        ('Allelopatia dodatnia', 'Allelopatia dodatnia'),
        ('Allelopatia ujemna', 'Allelopatia ujemna'),
  
    ]

    id_relacji = models.AutoField(primary_key=True)
    typ_relacji = models.CharField(max_length=50, choices=CHOICES)
    id_rosliny_1 = models.ForeignKey(Roslina, models.DO_NOTHING, db_column='id_rosliny_1', related_name='relacje_start')
    id_rosliny_2 = models.ForeignKey(Roslina, models.DO_NOTHING, db_column='id_rosliny_2', related_name='relacje_koniec')

    class Meta:
        db_table = 'relacja'
        indexes = [
            models.Index(fields=['typ_relacji'], name='idx_relacja_typ'),
        ]

    def __str__(self):
        return f"{self.id_rosliny_1} -> {self.typ_relacji} -> {self.id_rosliny_2}"