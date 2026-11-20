# Paweł Żaba | Nr Albumu 110381
import copy
import os
import sys
import sysconfig
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from silnik_danych.modele import RekordOsobowy
from silnik_danych.wielowatkowosc import przetworz_paczke_cpu


def sprawdz_info_gil() -> dict[str, object]:
    gil_wylaczony_kompilacja = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
    gil_aktywny = sys._is_gil_enabled() if hasattr(sys, "_is_gil_enabled") else True
    return {
        "wersja_pythona": sys.version.split()[0],
        "liczba_rdzeni": os.cpu_count() or 1,
        "interwal_przelaczania_s": sys.getswitchinterval(),
        "kompilacja_free_threading": gil_wylaczony_kompilacja,
        "gil_aktywny": gil_aktywny,
    }


def uruchom_benchmark_gil(
    paczki_wzorcowe: list[list[RekordOsobowy]],
    liczba_workerow: int = 4,
    iteracje_skrotu: int = 1200,
    sciezka_wykresu: str | Path = "wyniki/wykres_gil.png",
) -> dict[str, float]:
    info = sprawdz_info_gil()
    print("\n" + "=" * 62)
    print(" DIAGNOSTYKA ŚRODOWISKA I GLOBAL INTERPRETER LOCK (GIL)")
    print("=" * 62)
    print(f" Python:               {info['wersja_pythona']}")
    print(f" Liczba rdzeni CPU:    {info['liczba_rdzeni']}")
    print(f" Interwał wątków:      {info['interwal_przelaczania_s']} s")
    print(f" Free-threading build: {info['kompilacja_free_threading']}")
    print(f" GIL aktualnie aktywny:{info['gil_aktywny']}")
    print("-" * 62)

    wyniki: dict[str, float] = {}

    # 1. Wykonanie sekwencyjne (1 wątek, 1 proces)
    dane_sekw = copy.deepcopy(paczki_wzorcowe)
    start = time.perf_counter()
    for paczka in dane_sekw:
        przetworz_paczke_cpu(paczka, iteracje_skrotu)
    wyniki["Sekwencyjnie (1 wątek)"] = time.perf_counter() - start

    # 2. Wykonanie wielowątkowe (ThreadPoolExecutor - ograniczone przez GIL dla CPU)
    dane_watki = copy.deepcopy(paczki_wzorcowe)
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=liczba_workerow) as pula_watkow:
        zadania_w = [
            pula_watkow.submit(przetworz_paczke_cpu, paczka, iteracje_skrotu)
            for paczka in dane_watki
        ]
        for z in zadania_w:
            z.result()
    wyniki[f"Wątki ({liczba_workerow} threads)"] = time.perf_counter() - start

    # 3. Wykonanie wieloprocesowe (ProcessPoolExecutor - omija GIL na wielu rdzeniach)
    dane_procesy = copy.deepcopy(paczki_wzorcowe)
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=liczba_workerow) as pula_procesow:
        zadania_p = [
            pula_procesow.submit(przetworz_paczke_cpu, paczka, iteracje_skrotu)
            for paczka in dane_procesy
        ]
        for z in zadania_p:
            z.result()
    wyniki[f"Procesy ({liczba_workerow} processes)"] = time.perf_counter() - start

    czas_bazowy = wyniki["Sekwencyjnie (1 wątek)"]
    print(f"{'Tryb wykonania':<28} | {'Czas [s]':<10} | {'Przyspieszenie':<14}")
    print("-" * 62)
    for tryb, czas_s in wyniki.items():
        przyspieszenie = czas_bazowy / czas_s if czas_s > 0 else 0.0
        print(f"{tryb:<28} | {czas_s:<10.4f} | {przyspieszenie:>12.2f}x")
    print("=" * 62 + "\n")

    _zapisz_wykres_porownawczy(wyniki, Path(sciezka_wykresu))
    return wyniki


def _zapisz_wykres_porownawczy(wyniki: dict[str, float], sciezka: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[INFO] Biblioteka 'matplotlib' nie jest zainstalowana - pomijam generowanie wykresu.")
        return

    sciezka.parent.mkdir(parents=True, exist_ok=True)
    etykiety = list(wyniki.keys())
    czasy = list(wyniki.values())
    kolory = ["#6c757d", "#dc3545", "#198754"]

    plt.figure(figsize=(9, 5))
    slupki = plt.bar(etykiety, czasy, color=kolory[: len(etykiety)], width=0.5)
    plt.title("Porównanie wydajności zadań CPU-bound w Pythonie (wpływ GIL)")
    plt.ylabel("Czas wykonania [sekundy] (mniej = lepiej)")
    plt.grid(axis="y", linestyle="--", alpha=0.5)

    for slupek, czas in zip(slupki, czasy):
        plt.text(
            slupek.get_x() + slupek.get_width() / 2,
            slupek.get_height() + max(czasy) * 0.02,
            f"{czas:.3f} s",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    plt.tight_layout()
    plt.savefig(sciezka, dpi=150)
    plt.close()
    print(f"[WYKRES] Zapisano wykres benchmarku GIL do pliku: {sciezka}")