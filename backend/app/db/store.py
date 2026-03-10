"""Persistent key-value store backed by SQLite (WAL mode).

Replaces the in-memory dicts that were lost on every restart.
Data is stored as JSON blobs keyed by (namespace, id).
When ENCRYPTION_KEY is set, values are Fernet-encrypted at rest.
"""

import json
import logging
import sqlite3
from enum import Enum
from pathlib import Path
from threading import local

from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

_DB_PATH = Path(settings.upload_dir) / "store.db"
_local = local()
_fernet = None


def _get_fernet():
    global _fernet
    if _fernet is None and settings.encryption_key:
        from cryptography.fernet import Fernet

        _fernet = Fernet(settings.encryption_key.encode())
    return _fernet


def _get_conn() -> sqlite3.Connection:
    conn: sqlite3.Connection | None = getattr(_local, "conn", None)
    if conn is None:
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(_DB_PATH))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        _local.conn = conn
    return conn


def init_db() -> None:
    """Create the store table if it doesn't exist."""
    conn = _get_conn()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS store ("
        "  namespace TEXT NOT NULL,"
        "  key TEXT NOT NULL,"
        "  value TEXT NOT NULL,"
        "  PRIMARY KEY (namespace, key)"
        ")"
    )
    conn.commit()


def _default(obj: object) -> object:
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def save(namespace: str, key: str, data: dict) -> None:
    conn = _get_conn()
    raw = json.dumps(data, default=_default)
    f = _get_fernet()
    value = f.encrypt(raw.encode()).decode() if f else raw
    conn.execute(
        "INSERT OR REPLACE INTO store (namespace, key, value) VALUES (?, ?, ?)",
        (namespace, key, value),
    )
    conn.commit()


def load(namespace: str, key: str) -> dict | None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT value FROM store WHERE namespace = ? AND key = ?",
        (namespace, key),
    ).fetchone()
    if row is None:
        return None
    raw = row[0]
    f = _get_fernet()
    if f:
        try:
            raw = f.decrypt(raw.encode()).decode()
        except Exception:
            logger.warning(
                "Failed to decrypt key=%s/%s — returning raw", namespace, key
            )
    return json.loads(raw)
