from color_utils import (nome_para_hex, hex_para_hue, distancia_rgb, hex_para_rgb,
                         cor_mais_proxima, rgb_to_hex, hex_to_hsv_deg, hsv_deg_to_rgb)


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


# --- conversões RGB/HSV para sliders ---

def test_rgb_to_hex():
    assert rgb_to_hex(255, 0, 0) == "#FF0000"
    assert rgb_to_hex(0, 0, 0) == "#000000"
    assert rgb_to_hex(255, 255, 255) == "#FFFFFF"
    assert rgb_to_hex(10, 200, 90) == "#0AC85A"


def test_rgb_to_hex_clamps():
    assert rgb_to_hex(-5, 300, 128) == "#00FF80"


def test_hex_to_hsv_deg_red():
    h, s, v = hex_to_hsv_deg("#FF0000")
    assert h == 0
    assert s == 100
    assert v == 100


def test_hex_to_hsv_deg_green():
    h, s, v = hex_to_hsv_deg("#00FF00")
    assert h == 120
    assert s == 100
    assert v == 100


def test_hex_to_hsv_deg_gray():
    h, s, v = hex_to_hsv_deg("#808080")
    assert s == 0
    assert v == 50


def test_hsv_deg_to_rgb_red():
    assert hsv_deg_to_rgb(0, 100, 100) == (255, 0, 0)


def test_hsv_deg_to_rgb_white():
    assert hsv_deg_to_rgb(0, 0, 100) == (255, 255, 255)


def test_hsv_deg_to_rgb_black():
    assert hsv_deg_to_rgb(0, 0, 0) == (0, 0, 0)


def test_roundtrip_rgb_hsv_rgb():
    for rgb in [(255, 0, 0), (0, 128, 255), (123, 45, 200), (200, 200, 50), (10, 10, 10)]:
        h, s, v = hex_to_hsv_deg(rgb_to_hex(*rgb))
        back = hsv_deg_to_rgb(h, s, v)
        assert all(abs(a - b) <= 1 for a, b in zip(rgb, back))
