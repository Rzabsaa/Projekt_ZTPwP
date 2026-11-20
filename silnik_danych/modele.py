# Paweł Żaba | Nr Albumu 110381
from datetime import date
from silnik_danych.walidatory import (
    sprawdz_email,
    sprawdz_kod_pocztowy,
    sprawdz_pesel,
    sprawdz_telefon,
)


class RekordOsobowy:

    def __init__(
        self,
        imie: str,
        nazwisko: str,
        pesel: str,
        email: str,
        telefon: str,
        kod_pocztowy: str,
    ) -> None:
        self.imie = imie.strip().capitalize()
        self.nazwisko = nazwisko.strip().capitalize()
        self.pesel = pesel
        self.email = email
        self.telefon = telefon
        self.kod_pocztowy = kod_pocztowy
        self.skrot_bezpieczenstwa: str = ""

    @property
    def pesel(self) -> str:
        return self._pesel

    @pesel.setter
    def pesel(self, wartosc: str) -> None:
        poprawny, _ = sprawdz_pesel(wartosc)
        if not poprawny:
            raise ValueError(f"Nieprawidłowy numer PESEL: '{wartosc}'")
        self._pesel = wartosc.strip()

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, wartosc: str) -> None:
        poprawny, _ = sprawdz_email(wartosc)
        if not poprawny:
            raise ValueError(f"Nieprawidłowy adres e-mail: '{wartosc}'")
        self._email = wartosc.strip().lower()

    @property
    def telefon(self) -> str:
        return self._telefon

    @telefon.setter
    def telefon(self, wartosc: str) -> None:
        if not sprawdz_telefon(wartosc):
            raise ValueError(f"Nieprawidłowy numer telefonu: '{wartosc}'")
        self._telefon = wartosc.strip()

    @property
    def kod_pocztowy(self) -> str:
        return self._kod_pocztowy

    @kod_pocztowy.setter
    def kod_pocztowy(self, wartosc: str) -> None:
        if not sprawdz_kod_pocztowy(wartosc):
            raise ValueError(f"Nieprawidłowy kod pocztowy: '{wartosc}'")
        self._kod_pocztowy = wartosc.strip()

    @property
    def data_urodzenia(self) -> date:
        rok = int(self._pesel[0:2])
        miesiac = int(self._pesel[2:4])
        dzien = int(self._pesel[4:6])

        if miesiac > 20:
            rok += 2000
            miesiac -= 20
        else:
            rok += 1900

        return date(rok, miesiac, dzien)

    @classmethod
    def ze_slownika(cls, dane: dict[str, str]) -> "RekordOsobowy":
        return cls(
            imie=dane["imie"],
            nazwisko=dane["nazwisko"],
            pesel=dane["pesel"],
            email=dane["email"],
            telefon=dane["telefon"],
            kod_pocztowy=dane["kod_pocztowy"],
        )

    @staticmethod
    def naglowki_csv() -> list[str]:
        return [
            "imie",
            "nazwisko",
            "pesel",
            "data_urodzenia",
            "email",
            "telefon",
            "kod_pocztowy",
            "skrot_bezpieczenstwa",
        ]

    def do_slownika(self) -> dict[str, str]:
        return {
            "imie": self.imie,
            "nazwisko": self.nazwisko,
            "pesel": self.pesel,
            "data_urodzenia": self.data_urodzenia.isoformat(),
            "email": self.email,
            "telefon": self.telefon,
            "kod_pocztowy": self.kod_pocztowy,
            "skrot_bezpieczenstwa": self.skrot_bezpieczenstwa,
        }

    def __repr__(self) -> str:
        return f"RekordOsobowy(imie='{self.imie}', nazwisko='{self.nazwisko}', pesel='{self.pesel}')"