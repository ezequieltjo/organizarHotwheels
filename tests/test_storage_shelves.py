from models import ShelfConfig, Car, ParedeConfig
from storage import (insert_shelf, get_all_shelves, get_shelf_by_id,
                     update_shelf, delete_shelf, insert_car,
                     clear_positions, apply_positions, get_car_by_id,
                     get_wall_config, save_wall_config)


def test_insert_shelf():
    shelf = ShelfConfig(nome="P1", linhas=4, colunas=10)
    shelf_id = insert_shelf(shelf)
    assert shelf_id == 1


def test_get_all_shelves():
    insert_shelf(ShelfConfig(nome="P1", linhas=4, colunas=10))
    insert_shelf(ShelfConfig(nome="P2", linhas=3, colunas=8))
    shelves = get_all_shelves()
    assert len(shelves) == 2
    assert shelves[0].nome == "P1"


def test_get_shelf_by_id():
    insert_shelf(ShelfConfig(nome="P1", linhas=4, colunas=10))
    shelf = get_shelf_by_id(1)
    assert shelf.nome == "P1"
    assert shelf.linhas == 4


def test_update_shelf():
    insert_shelf(ShelfConfig(nome="P1", linhas=4, colunas=10))
    shelf = get_shelf_by_id(1)
    shelf.nome = "P1-Atualizado"
    shelf.parede_linha = 1
    shelf.parede_coluna = 0
    update_shelf(shelf)
    updated = get_shelf_by_id(1)
    assert updated.nome == "P1-Atualizado"
    assert updated.parede_linha == 1
    assert updated.parede_coluna == 0


def test_delete_shelf():
    insert_shelf(ShelfConfig(nome="P1", linhas=4, colunas=10))
    delete_shelf(1)
    assert get_shelf_by_id(1) is None


def test_apply_positions():
    insert_car(Car(modelo="A", cor_hex="#FF0000"))
    insert_car(Car(modelo="B", cor_hex="#0000FF"))
    apply_positions({1: (1, 0, 0), 2: (1, 0, 1)})
    car1 = get_car_by_id(1)
    assert car1.expositor_id == 1
    assert car1.posicao_linha == 0
    assert car1.posicao_coluna == 0


def test_clear_positions():
    insert_car(Car(modelo="A", cor_hex="#FF0000"))
    apply_positions({1: (1, 0, 0)})
    clear_positions()
    car = get_car_by_id(1)
    assert car.expositor_id is None
    assert car.posicao_linha is None


def test_get_wall_config_default():
    wall = get_wall_config()
    assert wall.linhas == 1
    assert wall.colunas == 1


def test_save_wall_config():
    save_wall_config(3, 4)
    wall = get_wall_config()
    assert wall.linhas == 3
    assert wall.colunas == 4


def test_save_wall_config_updates():
    save_wall_config(2, 2)
    save_wall_config(3, 1)
    wall = get_wall_config()
    assert wall.linhas == 3
    assert wall.colunas == 1
