# Paweł Żaba | Nr Albumu 110381
from typing import Iterable, Iterator, TypeVar

T = TypeVar("T")


class PorcjujacyIterator(Iterator[list[T]]):

    def __init__(
        self,
        zrodlo: Iterable[T],
        rozmiar_paczki: int,
        maksymalna_liczba_elementow: int,
    ) -> None:
        if rozmiar_paczki <= 0:
            raise ValueError("Rozmiar paczki musi być liczbą dodatnią.")
        if maksymalna_liczba_elementow < 0:
            raise ValueError("Maksymalna liczba elementów nie może być ujemna.")

        self._iterator = iter(zrodlo)
        self._rozmiar_paczki = rozmiar_paczki
        self._limit = maksymalna_liczba_elementow
        self._pobrane_ogolem = 0

    def __iter__(self) -> "PorcjujacyIterator[T]":
        """Zwraca sam obiekt iteratora zgodnie z protokołem Pythona."""
        return self

    def __next__(self) -> list[T]:
        """Zwraca kolejną paczkę elementów lub zgłasza StopIteration po osiągnięciu limitu."""
        if self._pobrane_ogolem >= self._limit:
            raise StopIteration

        paczka: list[T] = []
        while len(paczka) < self._rozmiar_paczki and self._pobrane_ogolem < self._limit:
            try:
                element = next(self._iterator)
                paczka.append(element)
                self._pobrane_ogolem += 1
            except StopIteration:
                break

        if not paczka:
            raise StopIteration

        return paczka