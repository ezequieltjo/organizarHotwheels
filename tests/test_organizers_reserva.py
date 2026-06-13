from models import Car, ShelfConfig, ParedeConfig
from organizers import (organize_rainbow, organize_gradient, organize_by_brand,
                        organize_by_fabricante, organize_by_year, organize_random,
                        organize_favorites_first, _filter_reserva)


def make_cars():
    return [
        Car(id=1, modelo="A", cor_hex="#FF0000", cor="vermelho", marca="Chevrolet",
            fabricante="Hot Wheels", ano=2023, favorito=False),
        Car(id=2, modelo="B", cor_hex="#0000FF", cor="azul", marca="Ford",
            fabricante="Matchbox", ano=2022, favorito=True),
        Car(id=3, modelo="C", cor_hex="#00FF00", cor="verde", marca="Chevrolet",
            fabricante="Hot Wheels", ano=2024, favorito=False),
    ]


def make_shelves():
    return [ShelfConfig(id=1, nome="P1", linhas=2, colunas=2)]


def test_filter_reserva_excludes_reserved():
    cars = make_cars()
    cars[1].reserva = True
    filtered = _filter_reserva(cars)
    assert len(filtered) == 2
    assert all(c.reserva is False for c in filtered)
    assert {c.id for c in filtered} == {1, 3}


def test_filter_reserva_empty_when_all_reserved():
    cars = make_cars()
    for c in cars:
        c.reserva = True
    filtered = _filter_reserva(cars)
    assert filtered == []


def test_filter_reserva_keeps_all_when_none_reserved():
    cars = make_cars()
    filtered = _filter_reserva(cars)
    assert len(filtered) == 3


def test_organize_rainbow_skips_reserva():
    cars = make_cars()
    cars[0].reserva = True
    result = organize_rainbow(cars, make_shelves())
    assert len(result) == 2
    assert 1 not in result
    assert set(result.keys()) == {2, 3}


def test_organize_gradient_skips_reserva():
    cars = make_cars()
    cars[0].reserva = True
    result = organize_gradient(cars, make_shelves())
    assert len(result) == 2
    assert 1 not in result


def test_organize_by_brand_skips_reserva():
    cars = make_cars()
    cars[2].reserva = True
    result = organize_by_brand(cars, make_shelves())
    assert len(result) == 2
    assert 3 not in result


def test_organize_random_skips_reserva():
    cars = make_cars()
    cars[1].reserva = True
    result = organize_random(cars, make_shelves())
    assert len(result) == 2
    assert 2 not in result


def test_organize_favorites_first_skips_reserva():
    """Favorito + reserva -> reserva ganha, nao posiciona."""
    cars = make_cars()
    cars[1].reserva = True
    cars[1].favorito = True
    result = organize_favorites_first(cars, make_shelves())
    assert len(result) == 2
    assert 2 not in result


def test_organize_all_reservas_returns_empty():
    cars = make_cars()
    for c in cars:
        c.reserva = True
    result = organize_rainbow(cars, make_shelves())
    assert result == {}


def test_organize_reserva_with_disabled_integration():
    """Reserva filter + disabled slots: ambos aplicados juntos."""
    shelves = [ShelfConfig(id=1, nome="P1", linhas=2, colunas=2)]
    disabled = {1: {"rows": {0}, "cells": set()}}
    cars = make_cars()
    cars[0].reserva = True
    result = organize_rainbow(cars, shelves, disabled=disabled)
    assert len(result) == 2
    assert 1 not in result
    for car_id, (sid, r, c) in result.items():
        assert r == 1
