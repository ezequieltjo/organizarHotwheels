from models import Car, ShelfConfig


def test_car_defaults():
    car = Car()
    assert car.id is None
    assert car.modelo == ""
    assert car.favorito is False
    assert car.expositor_id is None


def test_car_with_values():
    car = Car(id=1, modelo="Corvette", marca="Chevrolet", fabricante="Hot Wheels", ano=2023,
              cor="Vermelho", cor_hex="#FF0000", favorito=True)
    assert car.modelo == "Corvette"
    assert car.fabricante == "Hot Wheels"
    assert car.favorito is True


def test_shelf_config_defaults():
    shelf = ShelfConfig()
    assert shelf.id is None
    assert shelf.linhas == 0


def test_shelf_config_capacity():
    shelf = ShelfConfig(id=1, nome="Prateleira A", linhas=4, colunas=10)
    assert shelf.nome == "Prateleira A"
    assert shelf.linhas * shelf.colunas == 40


from models import GradientConfig


def test_gradient_config_defaults():
    cfg = GradientConfig()
    assert cfg.sat_threshold_pct == 12.0
    assert cfg.partial_strategy == "colorido"
    assert cfg.interior_strategy == "hue_value"


def test_gradient_config_is_frozen():
    import dataclasses
    cfg = GradientConfig()
    try:
        cfg.sat_threshold_pct = 50.0  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        return
    raise AssertionError("GradientConfig deve ser imutável (frozen)")
