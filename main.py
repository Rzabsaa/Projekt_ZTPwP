#Paweł Żaba | Nr albumu: 110381
import argparse
import logging
from silnik_danych.benchmark_gil import uruchom_benchmark_gil
from silnik_danych.dekoratory import mierz_czas
from silnik_danych.generatory import (
    polacz_strumienie,
    potok_walidacji,
    strumien_surowych_danych,
)
from silnik_danych.iteratory import PorcjujacyIterator
from silnik_danych.wielowatkowosc import (
    WielowatkowyEksporterPlikow,
    wzbogac_paczki_rownolegle,
)


def konfiguruj_logowanie(poziom: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, poziom.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@mierz_czas
def uruchom_przetwarzanie(
    liczba_rekordow: int,
    rozmiar_paczki: int,
    odsetek_bledow: float,
    liczba_procesow: int,
    liczba_watkow: int,
    katalog_wyjsciowy: str,
    uruchom_test_gil: bool,
) -> None:
    statystyki = {"wygenerowane": 0, "poprawne": 0, "odrzucone": 0}

    strumien_a = potok_walidacji(strumien_surowych_danych(odsetek_bledow), statystyki)
    strumien_b = potok_walidacji(strumien_surowych_danych(odsetek_bledow), statystyki)
    polaczony_strumien = polacz_strumienie(strumien_a, strumien_b)

    iterator_paczek = PorcjujacyIterator(
        zrodlo=polaczony_strumien,
        rozmiar_paczki=rozmiar_paczki,
        maksymalna_liczba_elementow=liczba_rekordow,
    )
    paczki = list(iterator_paczek)

    print(f"\n[GENEROWANIE] Wygenerowano surowych rekordów: {statystyki['wygenerowane']}")
    print(f"[WALIDACJA]   Poprawne rekordy: {statystyki['poprawne']} | Odrzucone błędne: {statystyki['odrzucone']}")
    print(f"[ITERATOR]    Podzielono dane na {len(paczki)} paczek (po maks. {rozmiar_paczki} rekordów).")

    if uruchom_test_gil:
        uruchom_benchmark_gil(
            paczki_wzorcowe=paczki,
            liczba_workerow=liczba_procesow,
            iteracje_skrotu=1000,
            sciezka_wykresu=f"{katalog_wyjsciowy}/wykres_gil.png",
        )

    print(f"[PROCESY]     Obliczanie skrótów bezpieczeństwa na {liczba_procesow} procesach...")
    wzbogacone_paczki = wzbogac_paczki_rownolegle(
        paczki=paczki,
        liczba_procesow=liczba_procesow,
        iteracje_skrotu=1000,
    )

    print(f"[WĄTKI]       Zapisywanie plików wynikowych przy użyciu {liczba_watkow} wątków...")
    eksporter = WielowatkowyEksporterPlikow(
        katalog_wyjsciowy=katalog_wyjsciowy,
        liczba_watkow=liczba_watkow,
    )
    eksporter.inicjalizuj()
    eksporter.eksportuj_paczki(wzbogacone_paczki)

    print(
        f"[SUKCES]      Zapisano {eksporter.zapisane_rekordy} rekordów "
        f"w {len(eksporter.utworzone_pliki)} plikach w katalogu '{katalog_wyjsciowy}/'.\n"
    )


def parsuj_argumenty() -> argparse.Namespace:
    """Obsługa parametrów linii poleceń (argparse - element dodatkowy z sekcji 9.3)."""
    parser = argparse.ArgumentParser(
        description="Generator i walidator danych testowych (Python 3.12+)"
    )
    parser.add_argument(
        "-n", "--rekordy",
        type=int,
        default=2000,
        help="Docelowa liczba poprawnych rekordów do wygenerowania (domyślnie: 2000)",
    )
    parser.add_argument(
        "-p", "--paczka",
        type=int,
        default=250,
        help="Liczba rekordów w pojedynczej paczce/pliku (domyślnie: 250)",
    )
    parser.add_argument(
        "-b", "--bledy",
        type=float,
        default=0.15,
        help="Odsetek celowo wstrzykiwanych błędnych danych 0.0-1.0 (domyślnie: 0.15)",
    )
    parser.add_argument(
        "--procesy",
        type=int,
        default=4,
        help="Liczba procesów roboczych dla zadań CPU-bound (domyślnie: 4)",
    )
    parser.add_argument(
        "--watki",
        type=int,
        default=4,
        help="Liczba wątków zapisujących pliki I/O (domyślnie: 4)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="wyniki",
        help="Katalog docelowy dla plików CSV/JSON (domyślnie: wyniki)",
    )
    parser.add_argument(
        "--bez-benchmarku",
        action="store_true",
        help="Pomija pomiar porównawczy GIL przed właściwym eksportem",
    )
    return parser.parse_args()


if __name__ == "__main__":
    konfiguruj_logowanie("WARNING")
    args = parsuj_argumenty()

    if args.rekordy <= 0 or args.paczka <= 0:
        raise SystemExit("Błąd: Liczba rekordów oraz rozmiar paczki muszą być większe od zera.")
    if not (0.0 <= args.bledy < 1.0):
        raise SystemExit("Błąd: Odsetek błędów musi mieścić się w przedziale [0.0, 1.0).")

    uruchom_przetwarzanie(
        liczba_rekordow=args.rekordy,
        rozmiar_paczki=args.paczka,
        odsetek_bledow=args.bledy,
        liczba_procesow=args.procesy,
        liczba_watkow=args.watki,
        katalog_wyjsciowy=args.output,
        uruchom_test_gil=not args.bez_benchmarku,
    )