# Backup da Coleção — Importar/Exportar/Apagar

**Data:** 2026-09-23

## Problema

A coleção vive em `db/collection.db` + `photos/`, versionada no GitHub. Não há forma
de: (1) levar a coleção para outra máquina sem git, (2) uma pessoa nova usar o site
(Streamlit Cloud) com base própria, (3) zerar a base sem apagar à mão.

## Solução

ZIP contendo `collection.db` + fotos referenciadas pelos carros (`cars.foto_path`).
Thumbs (`photos/thumbs/`) ficam fora — `ensure_thumb` regenera por mtime.

### Fluxos

- **Dono:** exporta ZIP no site → importa em outra máquina → altera → exporta →
  em casa importa → commit + push.
- **Visitante do Cloud:** apaga coleção (base vazia) → adiciona carros → baixa
  seu próprio ZIP.

### Módulo novo: `backup.py`

- `export_zip(db_path, photos_dir) -> bytes` — ZIP com `collection.db` (cópia
  consistente via `sqlite3.Connection.backup`, seguro com escrita concorrente no
  Cloud) + `photos/<arquivo>` de cada `foto_path` existente.
- `import_zip(db_path, photos_dir, data) -> int` — valida ZIP tem `collection.db`
  e schema de `cars`; substitui o DB atômico (`Path.replace`), extrai fotos
  (achatado em `photos/<basename>`), apaga fotos da base antiga que não existem
  na nova, roda `init_db()` (migrações cobrem schema antigo). Retorna nº de carros.
- `reset_collection(db_path, photos_dir, thumbs_dir) -> int` — coleta `foto_path`
  referenciados, apaga o arquivo do DB, limpa `thumbs/`, apaga só as fotos
  referenciadas (logo e arquivos não referenciados sobrevivem), recria schema
  vazio via `init_db()`.

### UI: aba "Backup" em `app.py`

1. **Exportar** — `st.download_button` com ZIP `colecao_YYYYMMDD.zip`. Zip
   cacheado (`st.cache_data` chaveado pelo mtime do DB) para não rezipar a cada
   rerun do Streamlit.
2. **Importar** — upload ZIP + aviso de que substitui tudo; em erro de ZIP
   inválido mostra `st.error` sem tocar na base atual.
3. **Apagar coleção** — checkbox "entendo que apaga tudo" destrava o botão.

Segurança do dono local: apagar coleção não apaga a versão do GitHub — um
`git restore .` recupera DB e fotos commitadas.

## Testes (`tests/test_backup.py`)

Ciclo completo com `tmp_path`: insere carros com foto → export contém db + foto →
reset esvazia e mantém arquivo não referenciado → import de outro ZIP substitui
carros/fotos e limpa foto órfã.
