import colorsys

NOMES_CORES = {
    "vermelho": "#FF0000",
    "azul": "#0000FF",
    "verde": "#00FF00",
    "amarelo": "#FFFF00",
    "laranja": "#FF8C00",
    "roxo": "#800080",
    "rosa": "#FFC0CB",
    "preto": "#000000",
    "branco": "#FFFFFF",
    "cinza": "#808080",
    "prata": "#C0C0C0",
    "dourado": "#FFD700",
    "marrom": "#8B4513",
    "bege": "#F5F5DC",
    "creme": "#FFFDD0",
    "verde musgo": "#4A5D23",
    "verde limao": "#32CD32",
    "azul marinho": "#000080",
    "azul claro": "#ADD8E6",
    "vermelho escuro": "#8B0000",
    "verde escuro": "#006400",
    "violeta": "#EE82EE",
    "magenta": "#FF00FF",
    "ciano": "#00FFFF",
    "turquesa": "#40E0D0",
    "salmao": "#FA8072",
    "chocolate": "#7B3F00",
}


def nome_para_hex(nome: str) -> str:
    if nome.startswith("#") and len(nome) == 7:
        return nome.upper()
    return NOMES_CORES.get(nome.lower().strip(), "#808080")


def hex_para_hue(hex_color: str) -> float:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    h, _l, _s = colorsys.rgb_to_hls(r, g, b)
    return h


def hex_para_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))


def distancia_rgb(hex1: str, hex2: str) -> float:
    r1, g1, b1 = hex_para_rgb(hex1)
    r2, g2, b2 = hex_para_rgb(hex2)
    return ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5


def cor_mais_proxima(hex_color: str) -> str:
    return min(NOMES_CORES, key=lambda n: distancia_rgb(hex_color, NOMES_CORES[n]))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """RGB (0-255) -> #RRGGBB, clampando valores fora do intervalo."""
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return f"#{r:02X}{g:02X}{b:02X}"


def hex_to_hsv_deg(hex_color: str) -> tuple[int, int, int]:
    """Hex -> (hue 0-360, saturation 0-100, value 0-100)."""
    r, g, b = (c / 255.0 for c in hex_para_rgb(hex_color))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return (round(h * 360), round(s * 100), round(v * 100))


def hsv_deg_to_rgb(h_deg: int, s_pct: int, v_pct: int) -> tuple[int, int, int]:
    """(hue 0-360, sat 0-100, val 0-100) -> RGB (0-255)."""
    h = (h_deg % 360) / 360.0
    s = max(0.0, min(1.0, s_pct / 100.0))
    v = max(0.0, min(1.0, v_pct / 100.0))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (round(r * 255), round(g * 255), round(b * 255))
