# Paweł Żaba | Nr Albumu 110381
import hashlib
import re

WZORZEC_PESEL = re.compile(
    r"^(?P<rok>\d{2})(?P<miesiac>\d{2})(?P<dzien>\d{2})(?P<seria>\d{4})(?P<kontrolna>\d)$"
)

WZORZEC_EMAIL = re.compile(
    r"^(?P<uzytkownik>[a-zA-Z0-9._%+-]+)@(?P<domena>[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$"
)

WZORZEC_TELEFON = re.compile(
    r"^(?:\+48\s?)?(?P<prefiks>\d{3})[-\s]?(?P<srodek>\d{3})[-\s]?(?P<koniec>\d{3})$"
)

WZORZEC_KOD_POCZTOWY = re.compile(
    r"^(?P<strefa>\d{2})-(?P<sektor>\d{3})$"
)

WAGI_PESEL = (1, 3, 7, 9, 1, 3, 7, 9, 1, 3)


def sprawdz_pesel(pesel: str) -> tuple[bool, dict[str, str] | None]:
    dopasowanie = WZORZEC_PESEL.fullmatch(pesel.strip())
    if not dopasowanie:
        return False, None

    cyfry = [int(znak) for znak in pesel]
    suma_wazona = sum(cyfra * waga for cyfra, waga in zip(cyfry[:10], WAGI_PESEL))
    cyfra_kontrolna = (10 - (suma_wazona % 10)) % 10

    if cyfra_kontrolna != cyfry[10]:
        return False, None

    return True, dopasowanie.groupdict()


def sprawdz_email(email: str) -> tuple[bool, str | None]:
    dopasowanie = WZORZEC_EMAIL.fullmatch(email.strip())
    if not dopasowanie:
        return False, None
    return True, dopasowanie.group("domena")


def sprawdz_telefon(telefon: str) -> bool:
    return WZORZEC_TELEFON.fullmatch(telefon.strip()) is not None


def sprawdz_kod_pocztowy(kod: str) -> bool:
    return WZORZEC_KOD_POCZTOWY.fullmatch(kod.strip()) is not None


def oblicz_skrot_bezpieczenstwa(dane: str, iteracje: int = 1500) -> str:
    wynik = dane
    for i in range(iteracje):
        wynik = f"{wynik}:{i}"
        if len(wynik) > 128:
            wynik = hashlib.sha256(wynik.encode("utf-8")).hexdigest()
    return wynik