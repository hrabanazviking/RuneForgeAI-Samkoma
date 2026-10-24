"""File storage behind one interface (roadmap B-007, D-17).

Callers ask for bytes by *key* and never learn a filesystem path —
so the local driver today can become an S3-compatible driver later
without any caller changing.
"""

from gpa.storage.base import StorageBackend
from gpa.storage.local import LocalStorage

__all__ = ["StorageBackend", "LocalStorage"]
