import pytest
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage

@pytest.fixture
def db():
    """Fixture to provide a clean TinyDB instance for each test."""
    return TinyDB(storage=MemoryStorage)

def test_remove_duplicate_doc_ids_no_keyerror(db):
    """AC-1: Calling table.remove(doc_ids=[id, id]) must not raise a KeyError."""
    doc_id = db.insert({'name': 'test'})
    # This should not raise KeyError
    db.table('_default').remove(doc_ids=[doc_id, doc_id])

def test_remove_returns_unique_removed_ids(db):
    """AC-2: The method must return a list of unique doc_ids that were successfully removed."""
    id1 = db.insert({'name': 'a'})
    id2 = db.insert({'name': 'b'})
    
    removed = db.table('_default').remove(doc_ids=[id1, id1, id2])
    
    assert sorted(removed) == sorted([id1, id2])
    assert len(db.table('_default')) == 0

def test_remove_mixed_valid_and_nonexistent_ids(db):
    """AC-3: Valid IDs must be removed, non-existent IDs must be ignored without exception."""
    id1 = db.insert({'name': 'a'})
    non_existent_id = 999
    
    # Should not raise KeyError for 999
    removed = db.table('_default').remove(doc_ids=[id1, non_existent_id])
    
    assert removed == [id1]
    assert len(db.table('_default')) == 0

def test_remove_empty_list(db):
    """AC-4: Passing an empty list [] to doc_ids must result in no changes and return []."""
    db.insert({'name': 'a'})
    
    removed = db.table('_default').remove(doc_ids=[])
    
    assert removed == []
    assert len(db.table('_default')) == 1

def test_remove_handles_iterators(db):
    """Edge Case: The implementation must handle doc_ids if passed as a generator."""
    id1 = db.insert({'name': 'a'})
    id2 = db.insert({'name': 'b'})
    
    def id_generator():
        yield id1
        yield id1
        yield id2
        
    removed = db.table('_default').remove(doc_ids=id_generator())
    
    assert sorted(removed) == sorted([id1, id2])
    assert len(db.table('_default')) == 0