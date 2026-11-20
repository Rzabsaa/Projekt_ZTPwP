# Paweł Żaba | Nr Albumu 110381
import unittest
from silnik_danych.generatory import strumien_surowych_danych
from silnik_danych.iteratory import PorcjujacyIterator
from silnik_danych.modele import RekordOsobowy
from silnik_danych.walidatory import (
    sprawdz_email,
    sprawdz_kod_pocztowy,
    sprawdz_pesel,
    sprawdz_telefon,
)
from silnik_danych.wielowatkowosc import WielowatkowyEksporterPlikow


class TestWalidatorowIModeli(unittest.TestCase):

    def test_poprawny_pesel(self) -> None:
        poprawny, grupy = sprawdz_pesel("44051401359")
        self.assertTrue(poprawny)
        self.assertIsNotNone(grupy)
        assert grupy is not None
        self.assertEqual(grupy["rok"], "44")
        self.assertEqual(grupy["miesiac"], "05")
        self.assertEqual(grupy["dzien"], "14")

    def test_bledna_suma_kontrolna_pesel(self) -> None:
        poprawny, grupy = sprawdz_pesel("44051401350")
        self.assertFalse(poprawny)
        self.assertIsNone(grupy)

    def test_walidacja_email(self) -> None:
        poprawny, domena = sprawdz_email("jan.kowalski@uczelnia.edu.pl")
        self.assertTrue(poprawny)
        self.assertEqual(domena, "uczelnia.edu.pl")

        poprawny_zly, _ = sprawdz_email("zly-adres-bez-malpy.pl")
        self.assertFalse(poprawny_zly)

    def test_walidacja_telefonu_i_kodu(self) -> None:
        self.assertTrue(sprawdz_telefon("+48 501-234-567"))
        self.assertTrue(sprawdz_telefon("501234567"))
        self.assertFalse(sprawdz_telefon("12-34"))

        self.assertTrue(sprawdz_kod_pocztowy("50-370"))
        self.assertFalse(sprawdz_kod_pocztowy("50370"))

    def test_model_rekordu_i_property(self) -> None:
        rekord = RekordOsobowy(
            imie="anna",
            nazwisko="nowak",
            pesel="44051401359",
            email="ANNA.NOWAK@WP.PL",
            telefon="600-700-800",
            kod_pocztowy="58-100",
        )
        self.assertEqual(rekord.imie, "Anna")
        self.assertEqual(rekord.email, "anna.nowak@wp.pl")
        self.assertEqual(rekord.data_urodzenia.year, 1944)

        with self.assertRaises(ValueError):
            rekord.pesel = "1111111111"