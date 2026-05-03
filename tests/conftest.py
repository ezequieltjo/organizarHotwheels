import pytest
from storage import set_db_path, init_db


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    db = tmp_path / "test.db"
    set_db_path(db)
    init_db()
    yield
    set_db_path(None)
