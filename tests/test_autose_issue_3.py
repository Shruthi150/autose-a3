import pytest
from tinydb import TinyDB, Query, where
from tinydb.storages import MemoryStorage

@pytest.fixture
def db():
    return TinyDB(storage=MemoryStorage)

@pytest.fixture
def table(db):
    return db.table('test')

def test_upsert_multiple_ac1_and_ac3(table):
    """AC-1 & AC-3: Upsert updates existing and inserts new, returning correct doc_ids."""
    User = Query()
    table.insert({'name': 'John', 'age': 20})  # doc_id 1
    
    updates = [
        ({'age': 21}, User.name == 'John'),      # Should update doc_id 1
        ({'name': 'Jane', 'age': 25}, User.name == 'Jane')  # Should insert
    ]
    
    doc_ids = table.upsert_multiple(updates)
    
    assert doc_ids == [1, 2]
    assert table.get(doc_id=1)['age'] == 21
    assert table.get(doc_id=2)['name'] == 'Jane'

def test_upsert_multiple_ac2_atomicity(table):
    """AC-2: The operation performs exactly one write to the storage backend."""
    # We wrap the storage to count write calls
    class WriteCountingStorage(MemoryStorage):
        def __init__(self):
            super().__init__()
            self.write_count = 0
        def write(self, data):
            self.write_count += 1
            super().write(data)

    db = TinyDB(storage=WriteCountingStorage)
    t = db.table('test')
    
    t.upsert_multiple([({'a': 1}, Query().a == 1), ({'a': 2}, Query().a == 2)])
    
    assert db.storage.write_count == 1

def test_upsert_multiple_ac4_empty_input(table):
    """AC-4: Empty input returns empty list and performs no operations."""
    doc_ids = table.upsert_multiple([])
    assert doc_ids == []
    assert len(table) == 0

def test_upsert_multiple_ac5_multiple_matches(table):
    """AC-5: If multiple documents match, all are updated and all IDs returned."""
    Item = Query()
    table.insert({'type': 'fruit', 'color': 'red'}) # 1
    table.insert({'type': 'fruit', 'color': 'red'}) # 2
    
    # Update all fruits to green
    doc_ids = table.upsert_multiple([({'color': 'green'}, Item.type == 'fruit')])
    
    assert sorted(doc_ids) == [1, 2]
    assert table.get(doc_id=1)['color'] == 'green'
    assert table.get(doc_id=2)['color'] == 'green'

def test_upsert_multiple_invalid_types(table):
    """Edge Case: Invalid types should raise TypeError or ValueError depending on implementation."""
    # The spec requires TypeError for non-dict documents.
    # We expect the implementation to validate input before attempting dict conversion.
    with pytest.raises((TypeError, ValueError)):
        table.upsert_multiple([("not a dict", Query().a == 1)])

def test_upsert_multiple_non_matching_query(table):
    """Edge Case: Non-matching query results in insertion."""
    User = Query()
    doc_ids = table.upsert_multiple([({'name': 'Bob'}, User.name == 'Bob')])
    
    assert len(doc_ids) == 1
    assert table.get(doc_id=doc_ids[0])['name'] == 'Bob'