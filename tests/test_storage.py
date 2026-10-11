from models import Car
from storage import insert_car, get_all_cars, get_car_by_id, update_car, delete_car


def test_insert_car():
    car = Car(modelo="Corvette", marca="Chevrolet", fabricante="Hot Wheels", ano=2023,
              cor="Vermelho", cor_hex="#FF0000")
    car_id = insert_car(car)
    assert car_id == 1


def test_get_all_cars():
    insert_car(Car(modelo="Corvette", cor_hex="#FF0000"))
    insert_car(Car(modelo="Mustang", cor_hex="#0000FF"))
    cars = get_all_cars()
    assert len(cars) == 2
    assert cars[0].modelo == "Corvette"
    assert cars[1].modelo == "Mustang"


def test_get_car_by_id():
    insert_car(Car(modelo="Corvette", ano=2023))
    car = get_car_by_id(1)
    assert car is not None
    assert car.modelo == "Corvette"
    assert car.ano == 2023


def test_get_car_by_id_not_found():
    assert get_car_by_id(999) is None


def test_update_car():
    insert_car(Car(modelo="Corvette", marca="Chevrolet"))
    car = get_car_by_id(1)
    car.modelo = "Camaro"
    update_car(car)
    updated = get_car_by_id(1)
    assert updated.modelo == "Camaro"


def test_update_car_promove_reset_created_at():
    """Sair da lista de desejos redefine created_at (data de adição à coleção)."""
    from storage import get_connection
    car_id = insert_car(Car(modelo="Supra", lista_desejos=True))
    conn = get_connection()
    conn.execute("UPDATE cars SET created_at='2026-01-01 00:00:00' WHERE id=?", (car_id,))
    conn.commit()
    conn.close()
    car = get_car_by_id(car_id)
    car.lista_desejos = False
    update_car(car)
    assert get_car_by_id(car_id).created_at != "2026-01-01 00:00:00"


def test_update_car_sem_promocao_mantem_created_at():
    """Edição comum (favorito, cor...) não altera created_at."""
    from storage import get_connection
    car_id = insert_car(Car(modelo="Supra"))
    conn = get_connection()
    conn.execute("UPDATE cars SET created_at='2026-01-01 00:00:00' WHERE id=?", (car_id,))
    conn.commit()
    conn.close()
    car = get_car_by_id(car_id)
    car.favorito = True
    update_car(car)
    assert get_car_by_id(car_id).created_at == "2026-01-01 00:00:00"


def test_update_car_created_at_parametro():
    """update_car com created_at altera a data de adição preservando update_at."""
    car_id = insert_car(Car(modelo="Supra"))
    car = get_car_by_id(car_id)
    update_car(car, created_at="2025-06-15 10:30:00")
    updated = get_car_by_id(car_id)
    assert updated.created_at == "2025-06-15 10:30:00"
    # sem o parâmetro, created_at permanece
    update_car(updated)
    assert get_car_by_id(car_id).created_at == "2025-06-15 10:30:00"


def test_lista_desejos_roundtrip():
    insert_car(Car(modelo="Supra", lista_desejos=True))
    car = get_car_by_id(1)
    assert car.lista_desejos is True
    car.lista_desejos = False
    update_car(car)
    assert get_car_by_id(1).lista_desejos is False


def test_delete_car():
    insert_car(Car(modelo="Corvette"))
    delete_car(1)
    assert get_car_by_id(1) is None
    assert len(get_all_cars()) == 0


def test_favorito_roundtrip():
    insert_car(Car(modelo="Corvette", favorito=True))
    car = get_car_by_id(1)
    assert car.favorito is True
