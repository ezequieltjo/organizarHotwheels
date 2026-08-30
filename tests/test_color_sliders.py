"""Testes dos sliders de cor: cor_key é a única fonte de verdade.

Reproduz o bug do snap colorida->cinza: estado HSV/RGB derivado com round()
travava saturação em 0, e o próximo movimento HSV virava a cor em cinza.
"""
from types import SimpleNamespace

import pytest

import color_sliders
from color_sliders import _on_hsv_change, _on_rgb_change, _slider_keys, render_color_sliders
from color_utils import hex_para_rgb


class _DummyCols:
    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


@pytest.fixture
def fake_st(monkeypatch):
    """st com session_state mutável e widgets no-op."""
    state: dict = {}

    def _noop(*_args, **_kwargs):
        return None

    fake = SimpleNamespace(
        session_state=state,
        slider=_noop,
        caption=_noop,
        markdown=_noop,
        color_picker=_noop,
        columns=lambda *_a, **_k: (_DummyCols(), _DummyCols()),
    )
    monkeypatch.setattr(color_sliders, "st", fake)
    return state


def test_on_rgb_change_writes_only_cor_key(fake_st):
    # Arrange
    fake_st.update({"k": "#FF0000", "k__R": 255, "k__G": 0, "k__B": 0})
    fake_st["k__R"] = 200  # usuário move R

    # Act
    _on_rgb_change("k")

    # Assert: só cor_key mudou; chaves HSV não tocadas pelo callback
    assert fake_st["k"] == "#C80000"
    assert "k__H" not in fake_st
    assert "k__S" not in fake_st


def test_on_hsv_change_writes_only_cor_key(fake_st):
    # Arrange
    _rk, _gk, _bk, hk, sk, vk = _slider_keys("k")
    fake_st.update({"k": "#FF0000", hk: 0, sk: 100, vk: 100})
    fake_st[sk] = 50  # usuário dessatura

    # Act
    _on_hsv_change("k")

    # Assert: cor_key atualizada; chaves RGB não tocadas pelo callback
    assert fake_st["k"] == "#FF8080"
    assert "k__R" not in fake_st
    assert "k__G" not in fake_st


def test_render_rederives_sliders_from_cor_key(fake_st):
    # Arrange: cor_key virou verde por fonte externa (color_picker/swatch)
    fake_st["k"] = "#00FF00"

    # Act
    render_color_sliders("k")

    # Assert: sliders RGB e HSV re-derivados do hex atual, não de estado velho
    rk, gk, bk, hk, sk, vk = _slider_keys("k")
    assert (fake_st[rk], fake_st[gk], fake_st[bk]) == (0, 255, 0)
    assert (fake_st[hk], fake_st[sk], fake_st[vk]) == (120, 100, 100)


def test_no_spurious_gray_snap_on_hue_move(fake_st):
    # Reproduz o snap: cor pastel; mover matiz NÃO pode virar cinza (r=g=b).
    # Arrange
    fake_st["k"] = "#C8A878"
    render_color_sliders("k")
    _, _, _, hk, _sk, _vk = _slider_keys("k")

    # Act: usuário move matiz 1 passo
    fake_st[hk] = (fake_st[hk] + 1) % 360
    _on_hsv_change("k")

    # Assert: resultado continua colorido (canais não iguais)
    r, g, b = hex_para_rgb(fake_st["k"])
    assert not (r == g == b), f"cor virou cinza: {fake_st['k']}"
