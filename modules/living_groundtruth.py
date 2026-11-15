"""Local-only Ground Truth storage and honest operational impact counters.

Enable on a controlled trusted deployment with BLOOM_ENABLE_LOCAL_SUBMISSIONS=1.
Never treat a submitted report as verified automatically.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path
import sqlite3
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRIVATE_DIR = ROOT / ".bloom_private"
CATEGORIES = {
    "Harvest activity", "Irrigation issue", "Visible vegetation change",
    "Land-use observation", "Field verification", "Other",
}
STATUSES = {"PENDING", "VERIFIED", "REJECTED"}


def local_submissions_enabled() -> bool:
    return os.environ.get("BLOOM_ENABLE_LOCAL_SUBMISSIONS") == "1"


def _storage(root: Path | str | None) -> Path:
    folder = Path(root) if root is not None else DEFAULT_PRIVATE_DIR
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    return folder


def _database(root: Path | str | None = None):
    db = sqlite3.connect(_storage(root) / "observations.sqlite3", timeout=5)
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("""
        CREATE TABLE IF NOT EXISTS reports(
            id TEXT PRIMARY KEY, case_id TEXT NOT NULL, area TEXT NOT NULL,
            observed_date TEXT NOT NULL, category TEXT NOT NULL,
            description TEXT NOT NULL, source_note TEXT NOT NULL,
            approx_lat REAL, approx_lon REAL, photo_name TEXT,
            photo_hash TEXT, status TEXT NOT NULL DEFAULT 'PENDING',
            created_utc TEXT NOT NULL, reviewed_utc TEXT)
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS activities(
            id TEXT PRIMARY KEY, case_id TEXT NOT NULL, kind TEXT NOT NULL,
            detail TEXT NOT NULL, created_utc TEXT NOT NULL)
    """)
    db.commit()
    return db


def sanitize_photo(content: bytes, name: str) -> tuple[bytes, str, str]:
    if not name.lower().endswith((".jpg", ".jpeg", ".png")):
        raise ValueError("Only JPEG and PNG uploads are accepted")
    if not content or len(content) > 2_000_000:
        raise ValueError("Photo must be nonempty and no larger than 2 MB")
    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
        with Image.open(BytesIO(content)) as image:
            if image.width * image.height > 12_000_000:
                raise ValueError("Image dimensions exceed safety limit")
            cleaned = image.convert("RGB")
            dest = BytesIO()
            # Redraw pixels into a fresh JPEG: EXIF/GPS metadata not retained.
            cleaned.save(dest, format="JPEG", quality=83)
            result = dest.getvalue()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("Invalid or unsafe image upload") from exc
    return result, ".jpg", sha256(result).hexdigest()


def submit_report(
    *, case_id: str, area: str, observed_date: str, category: str,
    description: str, source_note: str, consent: bool,
    approx_location: tuple[float, float] | None = None,
    location_consent: bool = False,
    photo: bytes | None = None, photo_filename: str = "",
    root: Path | str | None = None,
) -> str:
    """Store a private, unverified report. No name or email collected."""
    if not consent:
        raise ValueError("Informed consent is required")
    if not isinstance(case_id, str) or not (8 <= len(case_id) <= 64) or not case_id.isalnum():
        raise ValueError("Invalid case ID")
    if area not in {"area_a", "area_b"} or category not in CATEGORIES:
        raise ValueError("Invalid study area or observation category")
    from datetime import date
    try:
        obs_date = date.fromisoformat(observed_date)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid observation date") from exc
    if obs_date > date.today() or obs_date.year < 2000:
        raise ValueError("Observation date out of range")
    if not isinstance(description, str) or not (10 <= len(description.strip()) <= 2000):
        raise ValueError("Description must be 10–2000 characters")
    if not isinstance(source_note, str) or len(source_note) > 300:
        raise ValueError("Source description too long")
    latitude = longitude = None
    if approx_location is not None:
        if not location_consent:
            raise ValueError("Location-specific consent is required")
        lat, lon = approx_location
        if not (31.6 <= lat <= 32.2 and 35.2 <= lon <= 35.75):
            raise ValueError("Approximate coordinate outside study review area")
        latitude, longitude = round(lat, 2), round(lon, 2)
    clean_photo = photo_hash = photo_name = None
    if photo is not None:
        clean_photo, _, photo_hash = sanitize_photo(photo, photo_filename)
        photo_name = f"{uuid4().hex}.jpg"
    now = datetime.now(timezone.utc).isoformat()
    report_id = uuid4().hex
    folder = _storage(root)
    with _database(root) as db:
        # One report per case for a local prototype, preventing accidental rerun duplicates.
        if db.execute("SELECT 1 FROM reports WHERE case_id=?", (case_id,)).fetchone():
            raise ValueError("This investigation already has a field report")
        if clean_photo is not None:
            private_file = folder / photo_name
            with private_file.open("xb") as f:
                f.write(clean_photo)
            os.chmod(private_file, 0o600)
        try:
            db.execute("""
                INSERT INTO reports(id,case_id,area,observed_date,category,description,
                    source_note,approx_lat,approx_lon,photo_name,photo_hash,status,created_utc)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,'PENDING',?)
            """, (report_id, case_id, area, observed_date, category, description.strip(),
                  source_note.strip(), latitude, longitude, photo_name, photo_hash, now))
        except Exception:
            if photo_name:
                (folder / photo_name).unlink(missing_ok=True)
            raise
    return report_id


def review_report(report_id: str, status: str, *, root: Path | str | None = None) -> None:
    if status not in {"VERIFIED", "REJECTED"}:
        raise ValueError("Reviewer decision must be VERIFIED or REJECTED")
    with _database(root) as db:
        cursor = db.execute(
            "UPDATE reports SET status=?, reviewed_utc=? WHERE id=? AND status='PENDING'",
            (status, datetime.now(timezone.utc).isoformat(), report_id))
        if cursor.rowcount != 1:
            raise ValueError("Report not found or already reviewed")


def list_pending(*, root: Path | str | None = None) -> list[dict]:
    with _database(root) as db:
        db.row_factory = sqlite3.Row
        return [dict(r) for r in db.execute("""
            SELECT id,case_id,area,observed_date,category,description,source_note,
                   status,created_utc FROM reports WHERE status='PENDING'
            ORDER BY created_utc DESC LIMIT 100
        """).fetchall()]


def report_status(report_id: str, *, root: Path | str | None = None) -> str:
    with _database(root) as db:
        row = db.execute("SELECT status FROM reports WHERE id=?", (report_id,)).fetchone()
        return row[0] if row else "NOT_FOUND"


def record_activity(case_id: str, kind: str, detail: str, *, root: Path | str | None = None) -> None:
    if kind not in {"INVESTIGATION_COMPLETED", "ACTION_RECORDED", "CASE_REEVALUATED"}:
        raise ValueError("Unsupported activity")
    if not (isinstance(case_id, str) and 8 <= len(case_id) <= 64 and case_id.isalnum()):
        raise ValueError("Invalid case ID")
    if not isinstance(detail, str) or len(detail) > 200:
        raise ValueError("Invalid activity detail")
    with _database(root) as db:
        # Deduplicate per-case event, including across Streamlit reruns.
        exists = db.execute(
            "SELECT 1 FROM activities WHERE case_id=? AND kind=?",
            (case_id, kind)).fetchone()
        if not exists:
            db.execute("INSERT INTO activities VALUES (?,?,?,?,?)",
                       (uuid4().hex, case_id, kind, detail,
                        datetime.now(timezone.utc).isoformat()))


def impact_metrics(*, root: Path | str | None = None) -> dict:
    with _database(root) as db:
        return {
            "investigations_completed": db.execute(
                "SELECT COUNT(*) FROM activities WHERE kind='INVESTIGATION_COMPLETED'").fetchone()[0],
            "actions_recorded": db.execute(
                "SELECT COUNT(*) FROM activities WHERE kind='ACTION_RECORDED'").fetchone()[0],
            "field_submissions": db.execute("SELECT COUNT(*) FROM reports").fetchone()[0],
            "field_verified": db.execute(
                "SELECT COUNT(*) FROM reports WHERE status='VERIFIED'").fetchone()[0],
            "field_pending": db.execute(
                "SELECT COUNT(*) FROM reports WHERE status='PENDING'").fetchone()[0],
            "cases_reevaluated": db.execute(
                "SELECT COUNT(*) FROM activities WHERE kind='CASE_REEVALUATED'").fetchone()[0],
            "verified_environmental_impact": "Impact not yet verified.",
        }
