from color_utils import nome_para_hex, hex_para_hue, distancia_rgb, hex_para_rgb, cor_mais_proxima


def test_nome_para_hex_known():
    assert nome_para_hex("vermelho") == "#FF0000"
    assert nome_para_hex("Azul") == "#0000FF"


def test_nome_para_hex_already_hex():
    assert nome_para_hex("#FF0000") == "#FF0000"


def test_nome_para_hex_unknown():
    assert nome_para_hex("cor_inexistente") == "#808080"


def test_hex_para_hue_red():
    assert hex_para_hue("#FF0000") == 0.0


def test_hex_para_hue_green():
    h = hex_para_hue("#00FF00")
    assert 0.3 < h < 0.4


def test_hex_para_rgb():
    assert hex_para_rgb("#FF0000") == (255, 0, 0)
    assert hex_para_rgb("#0000FF") == (0, 0, 255)


def test_distancia_rgb_same():
    assert distancia_rgb("#FF0000", "#FF0000") == 0.0


def test_distancia_rgb_different():
    d = distancia_rgb("#FF0000", "#0000FF")
    assert d > 0


def test_cor_mais_proxima():
    assert cor_mais_proxima("#FF0000") == "vermelho"
