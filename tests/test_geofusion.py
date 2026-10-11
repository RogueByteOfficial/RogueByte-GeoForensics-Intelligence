"""
Automated Forensic Regression Tests for Temporal GeoFusion Engine
"""

import unittest
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.geospatial import GeoObservation, LocationCategory, LocationModality
from engine.geofusion import TemporalGeoFusionEngine, DefensibilityTier
from engine.temporal import parse_timestamp
from db.database import ForensicsDatabase, compute_sha256_of_bytes


class TestTemporalGeoFusion(unittest.TestCase):

    def setUp(self):
        self.engine = TemporalGeoFusionEngine(temporal_window_seconds=1800.0)

    def test_corroborated_gps_and_cell(self):
        """Tests that coinciding device GPS and cell sector result in CONCLUSIVE_CORROBORATED."""
        obs = [
            GeoObservation(
                observation_id="OBS-GPS",
                category=LocationCategory.DEVICE_OBSERVED,
                modality=LocationModality.DIRECT,
                timestamp_iso="2026-10-11T12:00:00Z",
                latitude=24.7136,
                longitude=46.6753,
                accuracy_radius_meters=30.0
            ),
            GeoObservation(
                observation_id="OBS-CELL",
                category=LocationCategory.CELLULAR_OBSERVATION,
                modality=LocationModality.INFERRED,
                timestamp_iso="2026-10-11T12:00:30Z",
                latitude=24.7150,
                longitude=46.6760,
                accuracy_radius_meters=1500.0
            )
        ]
        res = self.engine.fuse("2026-10-11T12:00:00Z", obs)
        self.assertEqual(res.defensibility_tier, DefensibilityTier.CONCLUSIVE_CORROBORATED)
        self.assertIsNotNone(res.primary_estimate_coordinates)
        self.assertEqual(len(res.contradictory_evidence_ids), 0)

    def test_impossible_velocity_contradiction(self):
        """Tests that displacement of thousands of kilometers in seconds triggers impossible velocity contradiction."""
        obs = [
            GeoObservation(
                observation_id="OBS-RIYADH",
                category=LocationCategory.DEVICE_OBSERVED,
                modality=LocationModality.DIRECT,
                timestamp_iso="2026-10-11T12:00:00Z",
                latitude=24.7136,
                longitude=46.6753,
                accuracy_radius_meters=20.0
            ),
            GeoObservation(
                observation_id="OBS-LONDON",
                category=LocationCategory.DEVICE_OBSERVED,
                modality=LocationModality.DIRECT,
                timestamp_iso="2026-10-11T12:00:10Z",  # 10 seconds later in London
                latitude=51.5074,
                longitude=-0.1278,
                accuracy_radius_meters=20.0
            )
        ]
        res = self.engine.fuse("2026-10-11T12:00:00Z", obs)
        self.assertEqual(res.defensibility_tier, DefensibilityTier.AMBIGUOUS_CONTRADICTORY)
        self.assertIn("OBS-RIYADH", res.contradictory_evidence_ids)
        self.assertIn("OBS-LONDON", res.contradictory_evidence_ids)

    def test_insufficient_evidence_when_out_of_window(self):
        """Tests that observations 10 hours away do not falsely establish location at incident time."""
        obs = [
            GeoObservation(
                observation_id="OBS-OLD",
                category=LocationCategory.DEVICE_OBSERVED,
                modality=LocationModality.DIRECT,
                timestamp_iso="2026-10-11T02:00:00Z",  # 10 hours prior
                latitude=24.7136,
                longitude=46.6753,
                accuracy_radius_meters=20.0
            )
        ]
        res = self.engine.fuse("2026-10-11T12:00:00Z", obs)
        self.assertEqual(res.defensibility_tier, DefensibilityTier.INSUFFICIENT_EVIDENCE)
        self.assertIsNone(res.primary_estimate_coordinates)

    def test_sha256_evidence_integrity_audit(self):
        """Tests that altering an ingested file triggers forensic integrity failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            vault_dir = os.path.join(tmpdir, "vault")
            db = ForensicsDatabase(db_path)

            db.create_case("CASE-TEST", "Test Case", "INV-1", "Lead", "2026-10-11T12:00:00Z", "target")

            # Create dummy evidence file
            src_file = os.path.join(tmpdir, "original_log.txt")
            with open(src_file, "w") as f:
                f.write("CONFIDENTIAL_FORENSIC_LOG_2026")

            ingest_res = db.ingest_evidence(
                case_id="CASE-TEST",
                evidence_id="EV-100",
                source_file_path=src_file,
                storage_vault_dir=vault_dir,
                source_type="SERVER_LOG",
                acquisition_method="PHYSICAL_IMAGE",
                investigator_id="INV-1",
                legal_auth_ref="WARRANT-2026-99"
            )

            # Verification 1: should pass
            passed, orig_hash, current_hash = db.verify_evidence_integrity("EV-100", "INV-1")
            self.assertTrue(passed)
            self.assertEqual(orig_hash, current_hash)

            # Simulate malicious tampering with stored file
            stored_file = ingest_res["stored_path"]
            os.chmod(stored_file, 0o666)  # allow write to test tampering
            with open(stored_file, "a") as f:
                f.write("MALICIOUS_ALTERATION")

            # Verification 2: should fail immediately
            passed_tampered, _, _ = db.verify_evidence_integrity("EV-100", "INV-1")
            self.assertFalse(passed_tampered)


if __name__ == "__main__":
    unittest.main()
