import io
import sqlite3
import zipfile

from models import Car
from storage import insert_car, get_all_cars, SCHEMA
from backup import export_zip, import_zip, reset_collection


def _zip_bytes(db_path, names):
    """ZIP sintático com collection.db + fotos."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.write(db_path, "collection.db")
        for n in names:
            zf.writestr(f"photos/{n}", f"conteudo {n}")
    return buf.getvalue()


def _mk_car(modelo, foto=""):
    return insert_car(Car(modelo=modelo, cor_hex="#FF0000", foto_path=foto))


def test_export_zip_contem_db_e_fotos(tmp_path):
    fotos = tmp_path / "photos"
    fotos.mkdir()
    (fotos / "a.jpg").write_bytes(b"foto a")
    _mk_car("Corsvette", "photos/a.jpg")
    _mk_car("Sem foto")

    data = export_zip(tmp_path / "test.db", fotos)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        assert "collection.db" in zf.namelist()
        assert "photos/a.jpg" in zf.namelist()


def test_export_zip_ignora_foto_ausente(tmp_path):
    _mk_car("Fantasma", "photos/inexistente.jpg")
    data = export_zip(tmp_path / "test.db", tmp_path)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        assert zf.namelist() == ["collection.db"]


def test_import_zip_substitui_colecao(tmp_path):
    fotos = tmp_path / "photos"
    fotos.mkdir()
    (fotos / "antiga.jpg").write_bytes(b"antiga")
    _mk_car("Velho", "photos/antiga.jpg")

    # base nova: 2 carros, 2 fotos
    outro = tmp_path / "outro.db"
    conn = sqlite3.connect(str(outro))
    conn.executescript(SCHEMA)
    conn.execute("INSERT INTO cars (modelo, foto_path) VALUES ('Novo1', 'photos/n1.jpg')")
    conn.execute("INSERT INTO cars (modelo, foto_path) VALUES ('Novo2', 'photos/n2.jpg')")
    conn.commit()
    conn.close()

    n = import_zip(tmp_path / "test.db", fotos, _zip_bytes(outro, ["n1.jpg", "n2.jpg"]))
    assert n == 2
    modelos = {c.modelo for c in get_all_cars()}
    assert modelos == {"Novo1", "Novo2"}
    assert (fotos / "n1.jpg").read_bytes() == b"conteudo n1.jpg"
    assert (fotos / "n2.jpg").read_bytes() == b"conteudo n2.jpg"
    assert not (fotos / "antiga.jpg").exists()  # foto órfã limpa


def test_import_zip_invalido_nao_toca_base(tmp_path):
    _mk_car("Original")
    fotos = tmp_path / "photos"
    fotos.mkdir()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("lixeira.txt", "nada")
    try:
        import_zip(tmp_path / "test.db", fotos, buf.getvalue())
        raised = False
    except ValueError:
        raised = True
    assert raised
    assert [c.modelo for c in get_all_cars()] == ["Original"]


def test_reset_collection_mantem_nao_referenciados(tmp_path):
    fotos = tmp_path / "photos"
    fotos.mkdir()
    thumbs = fotos / "thumbs"
    thumbs.mkdir()
    (thumbs / "a.jpg").write_bytes(b"thumb")
    (fotos / "a.jpg").write_bytes(b"referenciada")
    (fotos / "logo.png").write_bytes(b"logo")
    _mk_car("X", "photos/a.jpg")

    removed = reset_collection(tmp_path / "test.db", fotos, thumbs)
    assert removed == 1
    assert get_all_cars() == []
    assert not (fotos / "a.jpg").exists()
    assert (fotos / "logo.png").exists()      # não referenciada sobrevive
    assert not thumbs.exists()                # cache de thumbs limpo
