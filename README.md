## Paweł Żaba | Nr Albumu 110381
# Generator i walidator danych testowych (Python 3.12+)

Projekt zaliczeniowy z przedmiotu **Zaawansowane techniki programowania w języku Python**.

## 1. Opis projektu
Program służy do generowania i sprawdzania poprawności danych osobowych (imię, nazwisko, PESEL, e-mail, telefon, kod pocztowy). Dane są przetwarzane strumieniowo, żeby nie zapychać pamięci RAM przy większych paczkach. Poprawne rekordy przechodzą dodatkowo wielokrotne hashowanie SHA-256 (obciążenie procesora), a na koniec są zapisywane równolegle do plików CSV i JSON.

## 2. Jak uruchomić
Wymagany **Python 3.12+**. Biblioteka `matplotlib` jest potrzebna tylko do wygenerowania wykresu z pomiarów GIL.

```bash
# Instalacja biblioteki do wykresu (opcjonalnie)
pip install -r requirements.txt

# Uruchomienie programu z pomiarem GIL (8000 rekordów w paczkach po 1000)
python main.py -n 8000 -p 1000 --procesy 8 --watki 4

# Odpalenie testów jednostkowych
python -m unittest discover -s testy -v
```

## 3. Tabela mapowania zagadnień

| Zagadnienie | Gdzie w kodzie (plik / klasa / funkcja) |
| :--- | :--- |
| **Dekoratory funkcji** (zwykły + z parametrami + `wraps`) | `silnik_danych/dekoratory.py`: `mierz_czas()`, `ponow_probe(proby, opoznienie, wyjatki)` |
| **Dekoratory metod** (korzystający z `self` + wbudowane) | `silnik_danych/dekoratory.py`: `wymaga_gotowego_eksportera()`<br>`silnik_danych/modele.py`: `RekordOsobowy` (`@property` z setterem, `@classmethod`, `@staticmethod`) |
| **Iteratory** (`__iter__`, `__next__`, `StopIteration`) | `silnik_danych/iteratory.py`: klasa `PorcjujacyIterator` |
| **Generatory** (`yield`, wyrażenie generujące, `yield from`) | `silnik_danych/generatory.py`: `strumien_surowych_danych()`, `potok_walidacji()`, `polacz_strumienie()` |
| **Wyrażenia regularne** (`re.compile`, grupy nazwane) | `silnik_danych/walidatory.py`: `WZORZEC_PESEL`, `WZORZEC_EMAIL`, `WZORZEC_TELEFON`, `WZORZEC_KOD_POCZTOWY` |
| **Wątki** (`ThreadPoolExecutor`, `Queue`, `Lock`) | `silnik_danych/wielowatkowosc.py`: klasa `WielowatkowyEksporterPlikow` |
| **Procesy** (`ProcessPoolExecutor`, `if __name__ == "__main__":`) | `silnik_danych/wielowatkowosc.py`: `wzbogac_paczki_rownolegle()`, `przetworz_paczke_cpu()`<br>`main.py`: blok główny |
| **Pomiar GIL** (sekwencyjnie vs wątki vs procesy) | `silnik_danych/benchmark_gil.py`: `uruchom_benchmark_gil()`, `sprawdz_info_gil()` |

## 4. Wyniki benchmarku i wnioski o GIL

Testy zrobiłem u siebie na 16-rdzeniowym procesorze (Python 3.12.10, standardowy build z włączonym GIL). Sprawdziłem czas obliczania skrótów dla 8000 rekordów podzielonych na 8 paczek:

| Tryb wykonania | Czas wykonania [s] | Przyspieszenie względem wersji sekwencyjnej |
| :--- | :---: | :---: |
| Sekwencyjnie (1 wątek) | `1.5546 s` | `1.00x` |
| Wątki (`ThreadPoolExecutor`, 8 wątków) | `1.3823 s` | `1.12x` |
| Procesy (`ProcessPoolExecutor`, 8 procesów) | `0.5702 s` | `2.73x` |

Wykres wygenerowany z tego pomiaru zapisał się w `wyniki/wykres_gil.png`.

### Co wynika z pomiarów:
- **Wątki przy obliczeniach (CPU-bound) prawie nic nie dają:** Uruchomienie 8 wątków przyspieszyło skrypt tylko minimalnie (`1.12x`), bo w CPythonie blokada GIL puszcza w danym momencie tylko jeden wątek do wykonywania kodu Pythona. Ten niewielki skok wziął się stąd, że sam moduł `hashlib` jest napisany w C i na moment liczenia SHA-256 zwalnia GIL, ale cała reszta pętli i łączenie stringów dalej musiały na siebie czekać.
- **Procesy omijają GIL:** Dopiero `ProcessPoolExecutor` zbił czas z `1.5546 s` do `0.5702 s` (`2.73x` szybciej), bo każdy z 8 procesów dostał własny interpreter i osobny GIL na innym rdzeniu procesora.
- **Gdzie wątki mają sens:** Przy zapisywaniu 16 plików CSV i JSON na dysk (`WielowatkowyEksporterPlikow`) użyłem wątków, bo podczas operacji wejścia/wyjścia (I/O) interpreter i tak zwalnia GIL. Mimo wszystko trzeba było dodać `threading.Lock` przy zliczaniu zapisanych rekordów, żeby wątki nie nadpisywały sobie nawzajem licznika.

## 5. Problemy podczas pisania projektu
- **Błąd serializacji (`pickle`) przy procesach:** Na początku próbowałem wrzucić do `ProcessPoolExecutor` bezpośrednio obiekt generatora, ale wywalało błąd, bo procesy muszą sobie przesłać dane przez `pickle`, a generatora nie da się zserializować. Rozwiązałem to pisząc własny `PorcjujacyIterator`, który najpierw zbiera dane w zwykłe listy (paczki).
- **Zapętlanie procesów na Windowsie:** Przy odpalaniu `ProcessPoolExecutor` bez `if __name__ == "__main__":` skrypt próbował w kółko importować sam siebie i tworzyć nowe procesy (mechanizm `spawn` na Windowsie). Dodanie strażnika w `main.py` rozwiązało sprawę.
- **Polskie znaki w generowanych mailach:** Przy losowaniu nazwisk z polskimi znakami (np. *Woźniak*) walidator odrzucał poprawne rekordy, bo regex sprawdzał tylko znaki ASCII. Dodałem `str.maketrans` w generatorze, żeby zamieniał ogonki na zwykłe litery przy tworzeniu adresu e-mail.
EOF