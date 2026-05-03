import csv
import pytest
from pathlib import Path
from importer import import_file


@pytest.fixture
def csv_file(tmp_path):
    path = tmp_path / "cars.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["modelo", "marca", "ano", "cor", "serie_tipo"])
        w.writerow(["Corvette", "Mattel", 2023, "vermelho", "Mainline"])
        w.writerow(["Mustang", "Hot Wheels", 2022, "azul", "Premium"])
    return path


def test_import_csv(csv_file):
    cars = import_file(csv_file)
    assert len(cars) == 2
    assert cars[0].modelo == "Corvette"
    assert cars[0].cor_hex == "#FF0000"
    assert cars[1].marca == "Hot Wheels"
    assert cars[1].cor_hex == "#0000FF"


def test_import_csv_missing_columns(tmp_path):
    path = tmp_path / "partial.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["modelo", "cor"])
        w.writerow(["Corvette", "#FF0000"])
    cars = import_file(path)
    assert len(cars) == 1
    assert cars[0].modelo == "Corvette"
    assert cars[0].marca == ""
    assert cars[0].cor_hex == "#FF0000"


def test_import_csv_serie_tipo_alias(tmp_path):
    path = tmp_path / "alias.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["modelo", "Série Tipo"])
        w.writerow(["Corvette", "Treasure Hunt"])
    cars = import_file(path)
    assert cars[0].serie_tipo == "Treasure Hunt"


def test_import_csv_hex_cor(tmp_path):
    path = tmp_path / "hex.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["modelo", "cor"])
        w.writerow(["Corvette", "#00FF00"])
    cars = import_file(path)
    assert cars[0].cor_hex == "#00FF00"


def test_import_empty_csv(tmp_path):
    path = tmp_path / "empty.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["modelo", "marca"])
    cars = import_file(path)
    assert len(cars) == 0
