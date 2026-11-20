# Paweł Żaba | Nr Albumu 110381
import functools
import logging
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def mierz_czas(funkcja: F) -> F:

    @functools.wraps(funkcja)
    def opakowanie(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        wynik = funkcja(*args, **kwargs)
        czas_trwania = time.perf_counter() - start
        print(f"[CZAS] Funkcja '{funkcja.__name__}' wykonana w {czas_trwania:.4f} s")
        return wynik

    return opakowanie


def ponow_probe(
    proby: int = 3,
    opoznienie: float = 0.2,
    wyjatki: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:

    def dekorator(funkcja: F) -> F:
        @functools.wraps(funkcja)
        def opakowanie(*args: Any, **kwargs: Any) -> Any:
            for numer_proby in range(1, proby + 1):
                try:
                    return funkcja(*args, **kwargs)
                except wyjatki as blad:
                    logger.warning(
                        f"Próba {numer_proby}/{proby} dla '{funkcja.__name__}' nieudana: {blad}"
                    )
                    if numer_proby == proby:
                        raise RuntimeError(
                            f"Wyczerpano limit {proby} prób dla '{funkcja.__name__}'"
                        ) from blad
                    time.sleep(opoznienie)
            return None

        return opakowanie

    return dekorator


def wymaga_gotowego_eksportera(metoda: F) -> F:

    @functools.wraps(metoda)
    def opakowanie(self: Any, *args: Any, **kwargs: Any) -> Any:
        if not getattr(self, "czy_gotowy", False):
            raise RuntimeError(
                f"Błąd wywołania '{metoda.__name__}': Eksporter nie został jeszcze zainicjalizowany!"
            )
        return metoda(self, *args, **kwargs)

    return opakowanie