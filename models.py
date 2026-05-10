from dataclasses import dataclass
from typing import Optional


@dataclass
class Car:
    id: Optional[int] = None
    modelo: str = ""
    marca: str = ""
    fabricante: str = ""
    ano: int = 0
    cor: str = ""
    cor_hex: str = ""
    serie_tipo: str = ""
    favorito: bool = False
    foto_path: str = ""
    expositor_id: Optional[int] = None
    posicao_linha: Optional[int] = None
    posicao_coluna: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ShelfConfig:
    id: Optional[int] = None
    nome: str = ""
    linhas: int = 0
    colunas: int = 0
    parede_linha: int = 0
    parede_coluna: int = 0


@dataclass
class ParedeConfig:
    id: int = 1
    linhas: int = 1
    colunas: int = 1
