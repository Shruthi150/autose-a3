"""
A collection of update operations for TinyDB.

They are used for updates like this:

>>> db.update(delete('foo'), where('foo') == 2)

This would delete the ``foo`` field from all documents where ``foo`` equals 2.
"""


from collections.abc import Callable, MutableMapping
from typing import Any, Union


def delete(field: str) -> Callable[[MutableMapping], None]:
    """
    Delete a given field from the document.
    """
    def transform(doc: MutableMapping):
        del doc[field]

    return transform


def add(field: str, n: Union[int, float, str]) -> Callable[[MutableMapping], None]:
    """
    Add ``n`` to a given field in the document.

    Also works for strings (concatenation), matching the documented behavior.
    """
    def transform(doc: MutableMapping):
        doc[field] += n

    return transform


def subtract(field: str, n: Union[int, float]) -> Callable[[MutableMapping], None]:
    """
    Subtract ``n`` to a given field in the document.
    """
    def transform(doc: MutableMapping):
        doc[field] -= n

    return transform


def set(field: str, val: Any) -> Callable[[MutableMapping], None]:
    """
    Set a given field to ``val``.
    """
    def transform(doc: MutableMapping):
        doc[field] = val

    return transform


def increment(field: str, step: int = 1) -> Callable[[MutableMapping], None]:
    """
    Increment a given field in the document by ``step``.
    """
    def transform(doc: MutableMapping):
        doc[field] = doc.get(field, 0) + step

    return transform


def decrement(field: str, step: int = 1) -> Callable[[MutableMapping], None]:
    """
    Decrement a given field in the document by ``step``.
    """
    def transform(doc: MutableMapping):
        doc[field] = doc.get(field, 0) - step

    return transform
