"""SQLite job storage.

Schema: one table 'jobs' keyed by job_id (UUID) with a device_id column
for ownership. Each job stores the load input + classification result +
optional route check result as JSON blobs.

Database lives at /var/data/jobs.db when Render's persistent disk is mounted,
or backend/jobs.db locally.
"""
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

# Database path: Render persistent disk if available, else local file
RENDER_DISK_PATH = Path("/var/data")
LOCAL_DB_PATH = Path(__file__).parent.parent / "jobs.db"

if RENDER_DISK_PATH.exists() and os.access(RENDER_DISK_PATH, os.W_OK):
    DB_PATH = RENDER_DISK_PATH / "jobs.db"
else:
    DB_PATH = LOCAL_DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    name TEXT NOT NULL,
    load_input TEXT NOT NULL,       -- JSON
    classification TEXT NOT NULL,    -- JSON
    route_check TEXT,                -- JSON, nullable
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_jobs_device_id ON jobs(device_id);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
"""


def init_db() -> None:
    """Create tables if they don't exist. Called on app startup."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def get_conn():
    """Yield a SQLite connection with row factory set to dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_job(
    device_id: str,
    name: str,
    load_input: dict,
    classification: dict,
    route_check: dict | None = None,
) -> dict:
    """Create a new job. Returns the created job as a dict."""
    job_id = str(uuid.uuid4())
    now = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO jobs (id, device_id, name, load_input, classification, route_check, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                device_id,
                name,
                json.dumps(load_input),
                json.dumps(classification),
                json.dumps(route_check) if route_check else None,
                now,
                now,
            ),
        )
        conn.commit()
    return get_job(job_id)


def get_job(job_id: str) -> dict | None:
    """Fetch a single job by ID. Returns None if not found."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not row:
        return None
    return _row_to_dict(row)


def list_jobs(device_id: str, limit: int = 50) -> list[dict]:
    """List jobs for a device, newest first."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM jobs
            WHERE device_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (device_id, limit),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def delete_job(job_id: str, device_id: str) -> bool:
    """Delete a job. Only deletes if the device_id matches (ownership check)."""
    with get_conn() as conn:
        cursor = conn.execute(
            "DELETE FROM jobs WHERE id = ? AND device_id = ?",
            (job_id, device_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a SQLite row to a Python dict, parsing JSON columns."""
    return {
        "id": row["id"],
        "device_id": row["device_id"],
        "name": row["name"],
        "load_input": json.loads(row["load_input"]),
        "classification": json.loads(row["classification"]),
        "route_check": json.loads(row["route_check"]) if row["route_check"] else None,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
