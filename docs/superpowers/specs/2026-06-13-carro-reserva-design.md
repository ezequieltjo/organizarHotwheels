# Carro reserva — flag de exclusão da organização

**Data:** 2026-06-13
**Status:** Design

## Contexto

Coleção tem mais carros do que vagas nos expositores (162 carrinhos, 160 vagas). Após o recurso de "vagas bloqueadas" (commit `ea75dd1`), é possível marcar vagas como indisponíveis. Falta o oposto: marcar carros que não devem ser posicionados, mantendo-os na coleção.

Casos de uso:
- Carros reserva (sem slot físico)
- Carros duplicados (um pra exposição, outro guardado)
- Carros temporariamente indisponíveis (restauração, emprestados)

## Objetivo

Adicionar flag `reserva` em carros. Quando `True`:
- Carro permanece na lista da coleção
- Organizador pula o carro (não posiciona em expositor)
- Se estava posicionado, posição é limpa ao marcar

## Escopo

- Bool field `reserva` em `Car`
- Migration `ALTER TABLE cars ADD COLUMN reserva`
- Filter em todas `organize_*`
- UI: checkbox em forms add/edit + toggle na lista
- Marcador visual na lista (📦)
- Storage: `set_reserva(car_id, bool)` limpa posição quando True

Fora de escopo: tags múltiplas, categorias de reserva, data de reserva, motivo.

## Modelo de dados

Novo campo em `models.py::Car`:

```python
reserva: bool = False
```

Coluna em `cars` (storage.py SCHEMA):

```sql
reserva INTEGER NOT NULL DEFAULT 0
```

Migration em `init_db` (mesmo padrão `fabricante`):

```python
if "reserva" not in cols:
    conn.execute("ALTER TABLE cars ADD COLUMN reserva INTEGER NOT NULL DEFAULT 0")
```

Sem nova tabela. Default False = backward compat.

## Storage layer (`storage.py`)

**`insert_car`** — adiciona `reserva` ao INSERT:

```python
cursor = conn.execute(
    """INSERT INTO cars (modelo, marca, fabricante, ano, cor, cor_hex, serie_tipo,
       favorito, reserva, foto_path, expositor_id, posicao_linha, posicao_coluna, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
    (car.modelo, car.marca, car.fabricante, car.ano, car.cor, car.cor_hex, car.serie_tipo,
     int(car.favorito), int(car.reserva), car.foto_path, car.expositor_id,
     car.posicao_linha, car.posicao_coluna))
```

**`update_car`** — adiciona `reserva=?`:

```python
conn.execute(
    """UPDATE cars SET modelo=?, marca=?, fabricante=?, ano=?, cor=?, cor_hex=?,
       serie_tipo=?, favorito=?, reserva=?, foto_path=?, expositor_id=?,
       posicao_linha=?, posicao_coluna=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
    (car.modelo, car.marca, car.fabricante, car.ano, car.cor, car.cor_hex, car.serie_tipo,
     int(car.favorito), int(car.reserva), car.foto_path, car.expositor_id,
     car.posicao_linha, car.posicao_coluna, car.id))
```

**`_row_to_car`** — adiciona `reserva=bool(row["reserva"])`:

```python
return Car(
    id=row["id"], modelo=row["modelo"], marca=row["marca"],
    fabricante=row["fabricante"],
    ano=row["ano"], cor=row["cor"], cor_hex=row["cor_hex"],
    serie_tipo=row["serie_tipo"], favorito=bool(row["favorito"]),
    reserva=bool(row["reserva"]),
    foto_path=row["foto_path"], expositor_id=row["expositor_id"],
    posicao_linha=row["posicao_linha"], posicao_coluna=row["posicao_coluna"],
    created_at=row["created_at"], updated_at=row["updated_at"])
```

**Nova função `set_reserva`** (toggle atômico, limpa posição ao marcar True):

```python
def set_reserva(car_id: int, reserva: bool) -> None:
    """Marca/desmarca carro como reserva. Limpa posição ao marcar True."""
    conn = get_connection()
    if reserva:
        conn.execute(
            "UPDATE cars SET reserva=1, expositor_id=NULL, posicao_linha=NULL, posicao_coluna=NULL, "
            "updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (car_id,))
    else:
        conn.execute("UPDATE cars SET reserva=0, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                     (car_id,))
    conn.commit()
    conn.close()
```

`set_reserva(True)` limpa `expositor_id`, `posicao_linha`, `posicao_coluna` numa única transação — garante semântica "reserva = fora do expositor".

## Organizer integration (`organizers.py`)

Nova helper:

```python
def _filter_reserva(cars: list[Car]) -> list[Car]:
    return [c for c in cars if not c.reserva]
```

Todas 7 `organize_*` + `_gradient_2d_fill` filtram na primeira linha:

```python
def organize_rainbow(cars, shelves, wall=None, disabled=None):
    cars = _filter_reserva(cars)
    # ... resto inalterado
```

Padrão aplicado a:
- `organize_rainbow`, `organize_gradient`, `organize_by_brand`, `organize_by_fabricante`, `organize_by_year`, `organize_random`, `organize_favorites_first`

`_gradient_2d_fill` também chama `_filter_reserva` no topo.

`total_slots` — sem mudança (computa vagas, não carros).

## Visualizer

Sem mudança. Carros reserva não aparecem na grade porque `set_reserva(True)` limpa `expositor_id`, e o preview já filtra `positioned = [c for c in cars if c.expositor_id is not None]` (`app.py:408`).

## App UI (`app.py`)

### Lista Coleção (~linha 294)

Marcador 📦 na frente do nome do carro se reserva. Toggle botão ao lado do toggle favorito:

```python
if st.button("📦" if car.reserva else "·", key=f"reserva_{car.id}",
             help="Marcar como reserva (não posicionar)"):
    set_reserva(car.id, not car.reserva)
    refresh()
    st.rerun()
```

Display do nome do carro inclui marcador:

```python
reserva_marker = "📦 " if car.reserva else ""
# label: f"{reserva_marker}{fav_marker}{car.modelo}"
```

### Forms add/edit (~linhas 119, 203)

Checkbox nos forms:

```python
reserva = st.checkbox("Reserva (não posicionar em expositor)",
                      value=editing_car.reserva if editing_car else False)
```

Handler do form submit:

```python
if editing_car:
    editing_car.reserva = reserva
    if reserva and editing_car.expositor_id is not None:
        update_car(editing_car)
        set_reserva(editing_car.id, True)  # limpa posição
    else:
        update_car(editing_car)
else:
    insert_car(Car(modelo=modelo, ..., reserva=reserva))
```

### Warning de vagas insuficientes (~linha 398)

Ajusta contagem para usar carros não-reserva:

```python
active_cars = [c for c in cars if not c.reserva]
slots = total_slots(shelves, disabled)
if len(active_cars) > slots:
    st.warning(f"{len(active_cars)} carros ativos mas apenas {slots} vagas. "
               f"({len(cars) - len(active_cars)} reservas)")
```

## Casos borda

1. **Carro favorito + reserva** → favorito continua, mas não posiciona. `organize_favorites_first` também pula.
2. **Todos carros reserva** → `organize_*` retorna `{}` (após filtro).
3. **Carro posicionado marcado via toggle lista** → `set_reserva(True)` limpa posição.
4. **Carro posicionado marcado via form edit** → handler checa e chama `set_reserva`.
5. **Importar CSV/Excel** → `importer.py` constrói `Car`; dataclass default `reserva=False` cobre ausência de coluna. Sem mudança necessária.
6. **DB pré-migration** → `init_db` adiciona coluna via `ALTER TABLE`.
7. **Desmarcar reserva** → `set_reserva(False)` mantém `expositor_id` (que já é NULL normalmente). Não re-posiciona automaticamente; usuário roda "Gerar organização".

## Testes

**`tests/test_storage_reserva.py`** (novo):
- `test_insert_car_with_reserva_true` — roundtrip
- `test_update_car_preserves_reserva` — update não perde flag
- `test_set_reserva_true_clears_position` — limpa expositor_id e posição
- `test_set_reserva_false_keeps_null_position` — não re-posiciona
- `test_set_reserva_idempotent` — chamar 2x mesmo valor
- `test_migration_adds_reserva_column` — DB velho sem coluna → init_db adiciona

**`tests/test_organizers_reserva.py`** (novo):
- `test_filter_reserva_excludes_reserved`
- `test_organize_rainbow_skips_reserva`
- `test_organize_gradient_skips_reserva`
- `test_organize_favorites_first_skips_reserva` — favorito+reserva não posiciona
- `test_organize_random_skips_reserva`
- `test_organize_with_all_reservas_returns_empty`
- `test_organize_preserves_reserva_when_disabled_also_set` — integração com feature anterior
