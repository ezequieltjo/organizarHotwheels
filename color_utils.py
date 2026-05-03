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
