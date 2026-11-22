import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage, JSONStorage


@pytest.fixture(params=["memory", "json"])
def db(request, tmp_path):
    if request.param == "memory":
        database = TinyDB(storage=MemoryStorage)
    else:
        database = TinyDB(str(tmp_path / "db.json"), storage=JSONStorage)
    yield database
    database.close()
