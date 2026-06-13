from models import Car, ShelfConfig
from storage import (insert_car, update_car, get_car_by_id, set_reserva,
                     insert_shelf, apply_positions)


def test_insert_car_with_reserva_default_false():
    cid = insert_car(Car(modelo="A", cor_hex="#FF0000"))
    car = get_car_by_id(cid)
    assert car.reserva is False


def test_insert_car_with_reserva_true():
    cid = insert_car(Car(modelo="A", cor_hex="#FF0000", reserva=True))
    car = get_car_by_id(cid)
    assert car.reserva is True


def test_update_car_preserves_reserva():
    cid = insert_car(Car(modelo="A", cor_hex="#FF0000", reserva=True))
    car = get_car_by_id(cid)
    car.modelo = "B"
    update_car(car)
    refreshed = get_car_by_id(cid)
    assert refreshed.reserva is True
    assert refreshed.modelo == "B"


def test_update_car_toggles_reserva():
    cid = insert_car(Car(modelo="A", cor_hex="#FF0000", reserva=False))
    car = get_car_by_id(cid)
    car.reserva = True
    update_car(car)
    refreshed = get_car_by_id(cid)
    assert refreshed.reserva is True


def test_set_reserva_true_clears_position():
    """set_reserva(True) on positioned car clears expositor_id and position."""
    sid = insert_shelf(ShelfConfig(nome="P1", linhas=2, colunas=2))
    cid = insert_car(Car(modelo="A", cor_hex="#FF0000"))
    apply_positions({cid: (sid, 0, 0)})
    car = get_car_by_id(cid)
    assert car.expositor_id == sid  # sanity check
    set_reserva(cid, True)
    refreshed = get_car_by_id(cid)
    assert refreshed.reserva is True
    assert refreshed.expositor_id is None
    assert refreshed.posicao_linha is None
    assert refreshed.posicao_coluna is None


def test_set_reserva_false_keeps_null_position():
    """set_reserva(False) does NOT re-position (position stays NULL)."""
    cid = insert_car(Car(modelo="A", cor_hex="#FF0000"))
    set_reserva(cid, True)
    set_reserva(cid, False)
    refreshed = get_car_by_id(cid)
    assert refreshed.reserva is False
    assert refreshed.expositor_id is None


def test_set_reserva_idempotent():
    """Calling set_reserva twice with same value is safe."""
    cid = insert_car(Car(modelo="A", cor_hex="#FF0000"))
    set_reserva(cid, True)
    set_reserva(cid, True)
    refreshed = get_car_by_id(cid)
    assert refreshed.reserva is True


def test_set_reserva_false_when_already_false():
    cid = insert_car(Car(modelo="A", cor_hex="#FF0000"))
    set_reserva(cid, False)
    refreshed = get_car_by_id(cid)
    assert refreshed.reserva is False
