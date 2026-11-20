# Paweł Żaba | Nr Albumu 110381
import random
from typing import Generator, Iterable, Iterator
from silnik_danych.modele import RekordOsobowy
from silnik_danych.walidatory import WAGI_PESEL

IMIONA = (
    "Jan", "Anna", "Piotr", "Katarzyna", "Michał", "Agnieszka",
    "Krzysztof", "Magdalena", "Tomasz", "Barbara", "Paweł", "Ewa",
)

NAZWISKA = (
    "Nowak", "Kowalski", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński",
    "Lewandowski", "Zieliński", "Szymański", "Woźniak", "Dąbrowski", "Kozłowski",
)

DOMENY = ("gmail.com", "wp.pl", "onet.pl", "interia.pl", "uczelnia.edu.pl", "firma.pl")

POLSKIE_ZNAKI = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")


def _wygeneruj_poprawny_pesel() -> str:
    rok = random.randint(50, 99)
    miesiac = random.randint(1, 12)
    dzien = random.randint(1, 28)
    seria = random.randint(1000, 9999)

    baza = f"{rok:02d}{miesiac:02d}{dzien:02d}{seria:04d}"
    cyfry = [int(c) for c in baza]
    suma_wazona = sum(c * w for c, w in zip(cyfry, WAGI_PESEL))
    cyfra_kontrolna = (10 - (suma_wazona % 10)) % 10
    return f"{baza}{cyfra_kontrolna}"


def strumien_surowych_danych(odsetek_bledow: float = 0.1) -> Generator[dict[str, str], None, None]:
    while True:
        imie = random.choice(IMIONA)
        nazwisko = random.choice(NAZWISKA)
        pesel = _wygeneruj_poprawny_pesel()
        login = f"{imie}.{nazwisko}".lower().translate(POLSKIE_ZNAKI)
        email = f"{login}{random.randint(1, 999)}@{random.choice(DOMENY)}"
        telefon = f"+48 {random.randint(500, 899)}-{random.randint(100, 999)}-{random.randint(100, 999)}"
        kod = f"{random.randint(10, 99)}-{random.randint(100, 999)}"

        if random.random() < odsetek_bledow:
            rodzaj_bledu = random.choice(["pesel", "email", "kod"])
            if rodzaj_bledu == "pesel":
                pesel = "12345678900"
            elif rodzaj_bledu == "email":
                email = "niepoprawny_adres_bez_malpy.pl"
            elif rodzaj_bledu == "kod":
                kod = "00000"

        yield {
            "imie": imie,
            "nazwisko": nazwisko,
            "pesel": pesel,
            "email": email,
            "telefon": telefon,
            "kod_pocztowy": kod,
        }


def potok_walidacji(
    surowy_strumien: Iterable[dict[str, str]],
    statystyki: dict[str, int],
) -> Iterator[RekordOsobowy]:

    def proba_utworzenia(surowy: dict[str, str]) -> RekordOsobowy | None:
        statystyki["wygenerowane"] += 1
        try:
            rekord = RekordOsobowy.ze_slownika(surowy)
            statystyki["poprawne"] += 1
            return rekord
        except ValueError:
            statystyki["odrzucone"] += 1
            return None

    kandydaci = (proba_utworzenia(dane) for dane in surowy_strumien)
    return (rekord for rekord in kandydaci if rekord is not None)


def polacz_strumienie(*strumienie: Iterable[RekordOsobowy]) -> Generator[RekordOsobowy, None, None]:
    for strumien in strumienie:
        yield from strumien