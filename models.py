from dataclasses import dataclass
from typing import Optional


@dataclass
class Car:
    id: Optional[int] = None
    modelo: str = ""
    marca: str = ""
    ano: int = 0
    cor: str = ""
    cor_hex: str = ""
    serie_tipo: str = ""
    favorito: bool = False
    foto_path: str = ""
    expositor_id: Optional[int] = None
    posicao_linha: Optional[int] = None
    posicao_coluna: Optional[int] = None


@dataclass
class ShelfConfig:
    id: Optional[int] = None
    nome: str = ""
    linhas: int = 0
    colunas: int = 0
