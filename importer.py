import pandas as pd
from pathlib import Path
from models import Car
from color_utils import nome_para_hex


COL_MAP = {
    "modelo": "modelo",
    "marca": "marca",
    "fabricante": "fabricante",
    "ano": "ano",
    "cor": "cor",
    "serie_tipo": "serie_tipo",
    "serie tipo": "serie_tipo",
    "serie": "serie_tipo",
    "série_tipo": "serie_tipo",
    "série tipo": "serie_tipo",
    "série": "serie_tipo",
}


def import_file(filepath: str | Path) -> list[Car]:
    path = Path(filepath)
    if path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    df.columns = [COL_MAP.get(c.lower().strip(), c.lower().strip()) for c in df.columns]
    cars = []
    for _, row in df.iterrows():
        cor = str(row.get("cor", "")).strip()
        cor_hex = nome_para_hex(cor) if cor else ""
        car = Car(
            modelo=str(row.get("modelo", "")).strip(),
            marca=str(row.get("marca", "")).strip(),
            fabricante=str(row.get("fabricante", "")).strip(),
            ano=int(row.get("ano", 0)) if pd.notna(row.get("ano")) else 0,
            cor=cor,
            cor_hex=cor_hex,
            serie_tipo=str(row.get("serie_tipo", "")).strip(),
        )
        cars.append(car)
    return cars
