import csv
import io

import pytest
from importer import import_file


def _csv(tmp_path, nome, linhas):
    """Monta um CSV em tmp_path, confinado ao diretório temporário do pytest."""
    buf = io.StringIO()
    csv.writer(buf).writerows(linhas)
    path = tmp_path / nome
    if not path.resolve().is_relative_to(tmp_path.resolve()):
        raise ValueError(f"caminho fora do tmp_path: {path}")
    path.write_text(buf.getvalue(), encoding="utf-8")
    return path


@pytest.fixture
def csv_file(tmp_path):
    return _csv(tmp_path, "cars.csv", [
        ["modelo", "marca", "fabricante", "ano", "cor", "serie_tipo"],
        ["Corvette", "Chevrolet", "Hot Wheels", 2023, "vermelho", "Mainline"],
        ["Mustang", "Ford", "Matchbox", 2022, "azul", "Premium"],
    ])


def test_import_csv(csv_file):
    cars = import_file(csv_file)
    assert len(cars) == 2
    assert cars[0].modelo == "Corvette"
    assert cars[0].cor_hex == "#FF0000"
    assert cars[0].fabricante == "Hot Wheels"
    assert cars[1].marca == "Ford"
    assert cars[1].cor_hex == "#0000FF"


def test_import_csv_missing_columns(tmp_path):
    path = _csv(tmp_path, "partial.csv", [
        ["modelo", "cor"],
        ["Corvette", "#FF0000"],
    ])
    cars = import_file(path)
    assert len(cars) == 1
    assert cars[0].modelo == "Corvette"
    assert cars[0].marca == ""
    assert cars[0].fabricante == ""
    assert cars[0].cor_hex == "#FF0000"


def test_import_csv_serie_tipo_alias(tmp_path):
    path = _csv(tmp_path, "alias.csv", [
        ["modelo", "Série Tipo"],
        ["Corvette", "Treasure Hunt"],
    ])
    cars = import_file(path)
    assert cars[0].serie_tipo == "Treasure Hunt"


def test_import_csv_hex_cor(tmp_path):
    path = _csv(tmp_path, "hex.csv", [
        ["modelo", "cor"],
        ["Corvette", "#00FF00"],
    ])
    cars = import_file(path)
    assert cars[0].cor_hex == "#00FF00"


def test_import_empty_csv(tmp_path):
    path = _csv(tmp_path, "empty.csv", [
        ["modelo", "marca"],
    ])
    cars = import_file(path)
    assert len(cars) == 0
