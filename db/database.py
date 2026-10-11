"""
RogueByte GeoForensics Intelligence - Database & Cryptographic Audit
===================================================================
Provides SQLite (with optional SQLCipher encryption) database persistence,
immutable evidence storage with SHA-256 integrity checks, and append-only
tamper-evident audit logging using chained cryptographic hashes.
"""

import sqlite3
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    investigator_id TEXT NOT NULL,
    investigator_role TEXT NOT NULL,
    status TEXT DEFAULT 'OPEN',
    incident_time_utc TEXT,
    target_account TEXT,
    created_at_utc TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS evidence_items (
    evidence_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    original_filepath TEXT,
    stored_immutable_path TEXT NOT NULL,
    sha256_hash TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    mime_type TEXT,
    source_type TEXT NOT NULL,
    acquisition_time_utc TEXT NOT NULL,
    acquisition_method TEXT NOT NULL,
    investigator_id TEXT NOT NULL,
    legal_authorization_ref TEXT,
    parser_version TEXT DEFAULT '1.0.0',
    FOREIGN KEY(case_id) REFERENCES cases(case_id)
);

CREATE TABLE IF NOT EXISTS chain_of_custody (
    custody_id INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL,
    integrity_verified_sha256 TEXT NOT NULL,
    verification_passed INTEGER NOT NULL,
    notes TEXT,
    FOREIGN KEY(evidence_id) REFERENCES evidence_items(evidence_id)
);

CREATE TABLE IF NOT EXISTS geographic_observations (
    observation_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    category TEXT NOT NULL,
    modality TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL,
    original_timestamp_repr TEXT,
    latitude REAL,
    longitude REAL,
    accuracy_radius_meters REAL,
    crs TEXT DEFAULT 'EPSG:4326',
    reliability_notes TEXT,
    location_descriptor TEXT,
    metadata_json TEXT,
    FOREIGN KEY(case_id) REFERENCES cases(case_id),
    FOREIGN KEY(evidence_id) REFERENCES evidence_items(evidence_id)
);

CREATE TABLE IF NOT EXISTS provider_requests (
    request_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    reference_number TEXT NOT NULL,
    legal_authorization_ref TEXT NOT NULL,
    receiving_organization TEXT NOT NULL,
    request_scope TEXT NOT NULL,
    time_range_start_utc TEXT,
    time_range_end_utc TEXT,
    submission_timestamp_utc TEXT NOT NULL,
    response_timestamp_utc TEXT,
    preservation_status TEXT DEFAULT 'ACTIVE',
    response_hash_sha256 TEXT,
    retention_limitations TEXT,
    notes TEXT,
    FOREIGN KEY(case_id) REFERENCES cases(case_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_index INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT,
    timestamp_utc TEXT NOT NULL,
    action TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    details_json TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    entry_hash TEXT NOT NULL
);
"""


def compute_sha256_of_file(file_path: str) -> str:
    """Computes cryptographic SHA-256 hash of a file on disk."""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().lower()


def compute_sha256_of_bytes(data: bytes) -> str:
    """Computes SHA-256 hash of in-memory bytes."""
    return hashlib.sha256(data).hexdigest().lower()


class ForensicsDatabase:
    """
    Forensics database wrapper with cryptographic chain-of-custody
    and tamper-evident audit trail.
    """
    def __init__(self, db_path: str, encryption_key: Optional[str] = None):
        self.db_path = db_path
        self.encryption_key = encryption_key
        
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        # If SQLCipher is installed, apply key
        if self.encryption_key:
            try:
                self.conn.execute(f"PRAGMA key = '{self.encryption_key}';")
            except Exception:
                pass

        self._init_schema()

    def _init_schema(self):
        with self.conn:
            self.conn.executescript(SCHEMA_SQL)

    def log_audit(self, case_id: Optional[str], action: str, actor_id: str, details: Dict[str, Any]) -> str:
        """Appends a tamper-evident audit record with cryptographic hash chaining."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT entry_hash FROM audit_log ORDER BY log_index DESC LIMIT 1")
        row = cursor.fetchone()
        prev_hash = row["entry_hash"] if row else "GENESIS_0000000000000000000000000000000000000000000000000000000000000000"

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        details_str = json.dumps(details, sort_keys=True)

        payload = f"{prev_hash}|{case_id}|{now_utc}|{action}|{actor_id}|{details_str}".encode('utf-8')
        entry_hash = hashlib.sha256(payload).hexdigest()

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO audit_log (case_id, timestamp_utc, action, actor_id, details_json, prev_hash, entry_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (case_id, now_utc, action, actor_id, details_str, prev_hash, entry_hash)
            )
        return entry_hash

    def create_case(
        self,
        case_id: str,
        title: str,
        investigator_id: str,
        investigator_role: str,
        incident_time_utc: str,
        target_account: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO cases (case_id, title, investigator_id, investigator_role, incident_time_utc, target_account, created_at_utc, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (case_id, title, investigator_id, investigator_role, incident_time_utc, target_account, now_utc, notes)
            )
        self.log_audit(case_id, "CREATE_CASE", investigator_id, {"title": title, "target_account": target_account})
        return self.get_case(case_id)

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_cases(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cases ORDER BY created_at_utc DESC")
        return [dict(r) for r in cursor.fetchall()]

    def ingest_evidence(
        self,
        case_id: str,
        evidence_id: str,
        source_file_path: str,
        storage_vault_dir: str,
        source_type: str,
        acquisition_method: str,
        investigator_id: str,
        legal_auth_ref: str,
        mime_type: str = "application/octet-stream"
    ) -> Dict[str, Any]:
        """
        Secure evidence ingestion:
        1. Computes initial SHA-256 hash.
        2. Copies to immutable storage vault.
        3. Verifies copy hash equals source hash.
        4. Makes stored file read-only.
        5. Registers in database and chain of custody.
        """
        if not os.path.exists(source_file_path):
            raise FileNotFoundError(f"Evidence file not found: {source_file_path}")

        initial_sha256 = compute_sha256_of_file(source_file_path)
        file_size = os.path.getsize(source_file_path)
        filename = os.path.basename(source_file_path)

        os.makedirs(storage_vault_dir, exist_ok=True)
        immutable_dest = os.path.join(storage_vault_dir, f"{evidence_id}_{filename}")
        shutil.copy2(source_file_path, immutable_dest)

        # Verify copy integrity
        dest_sha256 = compute_sha256_of_file(immutable_dest)
        if dest_sha256 != initial_sha256:
            os.remove(immutable_dest)
            raise ValueError("Integrity failure during evidence ingestion copy!")

        # Make stored copy read-only (forensic immutability)
        try:
            os.chmod(immutable_dest, 0o444)
        except Exception:
            pass

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO evidence_items (
                    evidence_id, case_id, filename, original_filepath, stored_immutable_path,
                    sha256_hash, file_size_bytes, mime_type, source_type, acquisition_time_utc,
                    acquisition_method, investigator_id, legal_authorization_ref
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence_id, case_id, filename, source_file_path, immutable_dest,
                    dest_sha256, file_size, mime_type, source_type, now_utc,
                    acquisition_method, investigator_id, legal_auth_ref
                )
            )
            self.conn.execute(
                """
                INSERT INTO chain_of_custody (
                    evidence_id, action_type, actor_id, actor_role, timestamp_utc,
                    integrity_verified_sha256, verification_passed, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (evidence_id, "INGESTION", investigator_id, "PRIMARY_INVESTIGATOR", now_utc, dest_sha256, 1, "Initial acquisition and immutability lock")
            )

        self.log_audit(
            case_id, "EVIDENCE_INGESTED", investigator_id,
            {"evidence_id": evidence_id, "filename": filename, "sha256": dest_sha256, "size": file_size}
        )

        return {
            "evidence_id": evidence_id,
            "filename": filename,
            "sha256": dest_sha256,
            "stored_path": immutable_dest,
            "status": "SECURED_READONLY"
        }

    def verify_evidence_integrity(self, evidence_id: str, investigator_id: str) -> Tuple[bool, str, str]:
        """
        Recomputes hash on disk and compares against recorded database hash.
        Logs check to chain-of-custody table.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT stored_immutable_path, sha256_hash, case_id FROM evidence_items WHERE evidence_id = ?", (evidence_id,))
        row = cursor.fetchone()
        if not row:
            raise KeyError(f"Evidence {evidence_id} not found in database.")

        stored_path = row["stored_immutable_path"]
        recorded_hash = row["sha256_hash"]
        case_id = row["case_id"]

        if not os.path.exists(stored_path):
            passed = False
            current_hash = "FILE_MISSING"
        else:
            current_hash = compute_sha256_of_file(stored_path)
            passed = (current_hash == recorded_hash)

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO chain_of_custody (
                    evidence_id, action_type, actor_id, actor_role, timestamp_utc,
                    integrity_verified_sha256, verification_passed, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (evidence_id, "VERIFICATION_AUDIT", investigator_id, "FORENSIC_EXAMINER", now_utc, current_hash, 1 if passed else 0, "Periodic cryptographic integrity audit")
            )

        self.log_audit(
            case_id, "INTEGRITY_AUDIT", investigator_id,
            {"evidence_id": evidence_id, "passed": passed, "recorded_hash": recorded_hash, "current_hash": current_hash}
        )

        return (passed, recorded_hash, current_hash)

    def add_geo_observation(
        self,
        observation_id: str,
        case_id: str,
        evidence_id: str,
        category: str,
        modality: str,
        timestamp_utc: str,
        latitude: Optional[float],
        longitude: Optional[float],
        accuracy_radius_meters: Optional[float],
        original_timestamp_repr: str = "",
        reliability_notes: str = "",
        location_descriptor: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        meta_str = json.dumps(metadata or {}, ensure_ascii=False)
        with self.conn:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO geographic_observations (
                    observation_id, case_id, evidence_id, category, modality,
                    timestamp_utc, original_timestamp_repr, latitude, longitude,
                    accuracy_radius_meters, reliability_notes, location_descriptor, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    observation_id, case_id, evidence_id, category, modality,
                    timestamp_utc, original_timestamp_repr, latitude, longitude,
                    accuracy_radius_meters, reliability_notes, location_descriptor, meta_str
                )
            )

    def get_case_observations(self, case_id: str) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM geographic_observations WHERE case_id = ? ORDER BY timestamp_utc ASC", (case_id,))
        rows = cursor.fetchall()
        results = []
        for r in rows:
            d = dict(r)
            if d.get("metadata_json"):
                try:
                    d["metadata"] = json.loads(d["metadata_json"])
                except Exception:
                    d["metadata"] = {}
            results.append(d)
        return results

    def add_provider_request(
        self,
        request_id: str,
        case_id: str,
        reference_number: str,
        legal_authorization_ref: str,
        receiving_organization: str,
        request_scope: str,
        investigator_id: str,
        start_utc: Optional[str] = None,
        end_utc: Optional[str] = None,
        retention_limitations: str = "",
        notes: str = ""
    ):
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO provider_requests (
                    request_id, case_id, reference_number, legal_authorization_ref,
                    receiving_organization, request_scope, time_range_start_utc,
                    time_range_end_utc, submission_timestamp_utc, retention_limitations, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_id, case_id, reference_number, legal_authorization_ref,
                    receiving_organization, request_scope, start_utc, end_utc,
                    now_utc, retention_limitations, notes
                )
            )
        self.log_audit(
            case_id, "LEGAL_PROVIDER_REQUEST_CREATED", investigator_id,
            {"request_id": request_id, "org": receiving_organization, "ref": reference_number}
        )

    def list_provider_requests(self, case_id: str) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM provider_requests WHERE case_id = ? ORDER BY submission_timestamp_utc DESC", (case_id,))
        return [dict(r) for r in cursor.fetchall()]

    def get_audit_trail(self, case_id: Optional[str] = None) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        if case_id:
            cursor.execute("SELECT * FROM audit_log WHERE case_id = ? ORDER BY log_index ASC", (case_id,))
        else:
            cursor.execute("SELECT * FROM audit_log ORDER BY log_index ASC")
        return [dict(r) for r in cursor.fetchall()]
