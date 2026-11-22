import pytest
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage

@pytest.fixture
def db():
    """Fixture to provide a clean TinyDB instance for each test."""
    return TinyDB(storage=MemoryStorage)

def test_ac1_consistent_results_across_types(db):
    """AC-1: one_of() returns same results for list, tuple, set, and generator."""
    db.insert_multiple([{'val': 1}, {'val': 2}, {'val': 3}])
    
    q_list = Query().val.one_of([1, 2])
    q_tuple = Query().val.one_of((1, 2))
    q_set = Query().val.one_of({1, 2})
    q_gen = Query().val.one_of(x for x in [1, 2])
    
    expected = [{'val': 1}, {'val': 2}]
    
    assert db.search(q_list) == expected
    assert db.search(q_tuple) == expected
    assert db.search(q_set) == expected
    assert db.search(q_gen) == expected

def test_ac2_generator_full_consumption(db):
    """AC-2: If a generator is passed, search returns all matching documents."""
    db.insert_multiple([{'val': 'a'}, {'val': 'b'}, {'val': 'c'}, {'val': 'a'}])
    
    # Generator that yields 'a'
    gen = (x for x in ['a'])
    query = Query().val.one_of(gen)
    
    results = db.search(query)
    assert len(results) == 2
    assert results == [{'val': 'a'}, {'val': 'a'}]

def test_ac3_empty_generator(db):
    """AC-3: If an empty generator is passed, return False for all."""
    db.insert_multiple([{'val': 1}, {'val': 2}])
    
    empty_gen = (x for x in [])
    query = Query().val.one_of(empty_gen)
    
    assert db.search(query) == []

def test_ac4_reusability_and_idempotency(db):
    """AC-4: Query object must be reusable across multiple search calls."""
    db.insert_multiple([{'val': 1}, {'val': 2}])
    
    query = Query().val.one_of(x for x in [1])
    
    # First call
    assert db.search(query) == [{'val': 1}]
    # Second call (should not be exhausted)
    assert db.search(query) == [{'val': 1}]

def test_edge_case_mixed_types(db):
    """Edge Case: Handle mixed types (integers, booleans, None)."""
    db.insert_multiple([{'val': 1}, {'val': True}, {'val': None}, {'val': 'string'}])
    
    query = Query().val.one_of([1, True, None])
    
    results = db.search(query)
    # Note: In Python, 1 == True. TinyDB equality checks usually respect this.
    assert len(results) == 3
    assert {'val': 1} in results
    assert {'val': True} in results
    assert {'val': None} in results