# Paweł Żaba | Nr Albumu 110381
import csv
import json
import logging
import os
import queue
import threading
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from silnik_danych.dekoratory import ponow_probe, wymaga_gotowego_eksportera
from silnik_danych.modele import RekordOsobowy
from silnik_danych.walidatory import oblicz_skrot_bezpieczenstwa

logger = logging.getLogger(__name__)
ZNAK_KONCA = None


def przetworz_paczke_cpu(paczka: list[RekordOsobowy], iteracje_skrotu: int = 800) -> list[RekordOsobowy]:
    for rekord in paczka:
        surowy_ciag = f"{rekord.pesel}:{rekord.email}:{rekord.nazwisko}"
        rekord.skrot_bezpieczenstwa = oblicz_skrot_bezpieczenstwa(
            surowy_ciag, iteracje=iteracje_skrotu
        )
    return paczka


def wzbogac_paczki_rownolegle(
    paczki: list[list[RekordOsobowy]],
    liczba_procesow: int | None = None,
    iteracje_skrotu: int = 800,
) -> list[list[RekordOsobowy]]:
    if not paczki:
        return []

    maks_procesow = liczba_procesow or os.cpu_count() or 2
    with ProcessPoolExecutor(max_workers=maks_procesow) as pula:
        zadania = [
            pula.submit(przetworz_paczke_cpu, paczka, iteracje_skrotu)
            for paczka in paczki
        ]
        return [zadanie.result() for zadanie in zadania]


class WielowatkowyEksporterPlikow:

    def __init__(self, katalog_wyjsciowy: str | Path, liczba_watkow: int = 4) -> None:
        self.katalog_wyjsciowy = Path(katalog_wyjsciowy)
        self.liczba_watkow = liczba_watkow
        self.czy_gotowy: bool = False
        self._kolejka: queue.Queue[tuple[int, list[RekordOsobowy]] | None] = queue.Queue(maxsize=10)
        self._blokada_licznika = threading.Lock()
        self.zapisane_rekordy: int = 0
        self.utworzone_pliki: list[str] = []

    def inicjalizuj(self) -> None:
        self.katalog_wyjsciowy.mkdir(parents=True, exist_ok=True)
        self.czy_gotowy = True
        logger.info(f"Eksporter zainicjalizowany w katalogu: {self.katalog_wyjsciowy}")

    @ponow_probe(proby=3, opoznienie=0.1, wyjatki=(OSError,))
    def _zapisz_pojedyncza_paczke(self, numer_paczki: int, paczka: list[RekordOsobowy]) -> None:
        sciezka_csv = self.katalog_wyjsciowy / f"dane_partia_{numer_paczki:03d}.csv"
        sciezka_json = self.katalog_wyjsciowy / f"dane_partia_{numer_paczki:03d}.json"

        slowniki = [rekord.do_slownika() for rekord in paczka]

        with open(sciezka_csv, mode="w", newline="", encoding="utf-8") as plik_csv:
            pisarz = csv.DictWriter(plik_csv, fieldnames=RekordOsobowy.naglowki_csv())
            pisarz.writeheader()
            pisarz.writerows(slowniki)

        with open(sciezka_json, mode="w", encoding="utf-8") as plik_json:
            json.dump(slowniki, plik_json, ensure_ascii=False, indent=2)

        with self._blokada_licznika:
            self.zapisane_rekordy += len(paczka)
            self.utworzone_pliki.extend([sciezka_csv.name, sciezka_json.name])

    def _konsument_watku(self) -> None:
        while True:
            zadanie = self._kolejka.get()
            try:
                if zadanie is ZNAK_KONCA:
                    break
                numer_paczki, paczka = zadanie
                self._zapisz_pojedyncza_paczke(numer_paczki, paczka)
            finally:
                self._kolejka.task_done()

    @wymaga_gotowego_eksportera
    def eksportuj_paczki(self, paczki: list[list[RekordOsobowy]]) -> None:
        with ThreadPoolExecutor(max_workers=self.liczba_watkow) as pula_watkow:
            konsumenci = [
                pula_watkow.submit(self._konsument_watku)
                for _ in range(self.liczba_watkow)
            ]

            for indeks, paczka in enumerate(paczki, start=1):
                self._kolejka.put((indeks, paczka))

            for _ in range(self.liczba_watkow):
                self._kolejka.put(ZNAK_KONCA)

            self._kolejka.join()
            for konsument in konsumenci:
                konsument.result()