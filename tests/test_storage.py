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
