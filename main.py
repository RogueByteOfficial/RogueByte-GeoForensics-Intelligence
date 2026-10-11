"""
RogueByte GeoForensics Intelligence
===================================
Main Application Entry Point.
Launches the standalone PySide6 Windows desktop interface, or runs in CLI / forensic headless mode.
"""

import sys
import os
import argparse
from datetime import datetime, timezone

from db.database import ForensicsDatabase
from engine.geofusion import TemporalGeoFusionEngine
from engine.geospatial import GeoObservation, LocationCategory, LocationModality
from reports.report_generator import ForensicReportGenerator


def run_cli_demo(db_path: str = "forensics_data.db"):
    """Executes a complete forensic demonstration via command-line."""
    print("=" * 70)
    print("  ROGUEBYTE GEOFORENSICS INTELLIGENCE - CLI ENGINE DEMO")
    print("=" * 70)

    db = ForensicsDatabase(db_path)
    case_id = "CASE-2026-ALPHA"
    case = db.get_case(case_id)
    if not case:
        case = db.create_case(
            case_id=case_id,
            title="واقعة اتصال مشبوه عبر وسائل التواصل وتضارب مواقع IP مع الأبراج",
            investigator_id="INV-LEAD-704",
            investigator_role="كبير خبراء الأدلة الرقمية",
            incident_time_utc="2026-10-11T14:30:00Z",
            target_account="target_suspect_01",
            notes="فحص دفاعي لموقع الجهاز وقت إجراء المكالمة الصوتية"
        )
        print(f"[+] تم إنشاء القضية الجنائية: {case_id}")

    # Run Temporal GeoFusion Engine on synthetic multi-sensor evidence
    print("\n[+] تشغيل محرك Temporal GeoFusion على الأدلة المرصودة...")
    engine = TemporalGeoFusionEngine(temporal_window_seconds=1800.0)

    observations = [
        GeoObservation(
            observation_id="OBS-001",
            category=LocationCategory.DEVICE_OBSERVED,
            modality=LocationModality.DIRECT,
            timestamp_iso="2026-10-11T14:30:00Z",
            latitude=24.7136,
            longitude=46.6753,
            accuracy_radius_meters=25.0,
            reliability_notes="مستشعر GPS المباشر من هاتف الهدف بنصف قطر دقة 25 متر"
        ),
        GeoObservation(
            observation_id="OBS-002",
            category=LocationCategory.CELLULAR_OBSERVATION,
            modality=LocationModality.INFERRED,
            timestamp_iso="2026-10-11T14:30:10Z",
            latitude=24.7150,
            longitude=46.6780,
            accuracy_radius_meters=1800.0,
            reliability_notes="قطاع تغطية برج الاتصالات الخلوي STC رقم 40221"
        ),
        GeoObservation(
            observation_id="OBS-003",
            category=LocationCategory.IP_NETWORK_ESTIMATE,
            modality=LocationModality.INFERRED,
            timestamp_iso="2026-10-11T14:30:05Z",
            latitude=50.1109,
            longitude=8.6821,
            accuracy_radius_meters=25000.0,
            reliability_notes="عنوان IP لمركز بيانات VPN في ألمانيا (لا يعكس موقع الشخص الفيزيائي)"
        )
    ]

    result = engine.fuse("2026-10-11T14:30:00Z", observations)

    print(f"[*] مستوى الموثوقية الجنائية (Tier): {result.defensibility_tier}")
    print(f"[*] الإحداثيات المرجحة دفاعياً: {result.primary_estimate_coordinates}")
    print(f"[*] نصف قطر عدم اليقين: +/- {result.estimated_accuracy_radius_meters} متر")
    print(f"[*] الخلاصة الجنائية:")
    print(f"    {result.defensible_summary}")

    print("\n[*] التناقضات والتوضيحات الفنية:")
    for calc in result.detailed_calculations:
        if "finding" in calc:
            print(f"    - {calc['pair']}: {calc['finding']}")

    # Export report
    report_file = os.path.abspath("forensic_report_demo.html")
    ForensicReportGenerator.generate_html_report(
        case=case,
        evidence_items=[
            {"evidence_id": "EV-001", "filename": "cdr_records.csv", "source_type": "مزوّد الاتصالات", "acquisition_time_utc": "2026-10-11T14:35:00Z", "file_size_bytes": 1024, "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}
        ],
        chain_of_custody=[
            {"timestamp_utc": "2026-10-11T14:35:00Z", "evidence_id": "EV-001", "action_type": "INGESTION", "actor_id": "INV-704", "actor_role": "PRIMARY", "verification_passed": 1, "notes": "إيداع أولي وتشفير"}
        ],
        observations=[o.to_dict() for o in observations],
        fusion_result=result.to_dict(),
        audit_trail=db.get_audit_trail(case_id),
        output_filepath=report_file
    )
    print(f"\n[+] تم تصدير التقرير الجنائي المعتمد بنجاح: {report_file}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="RogueByte GeoForensics Intelligence")
    parser.add_argument("--cli", action="store_true", help="تشغيل المحرك في وضع سطر الأوامر (Headless CLI)")
    parser.add_argument("--demo", action="store_true", help="تنفيذ سيناريو جنائي تجريبي وحساب النتائج")
    parser.add_argument("--db", type=str, default="forensics_data.db", help="مسار ملف قاعدة البيانات SQLite")
    args = parser.parse_args()

    if args.cli or args.demo:
        run_cli_demo(args.db)
        return

    # Attempt to launch PySide6 desktop GUI
    try:
        from PySide6.QtWidgets import QApplication
        from gui.main_window import RogueByteMainWindow

        app = QApplication(sys.argv)
        db = ForensicsDatabase(args.db)
        window = RogueByteMainWindow(db)
        window.show()
        sys.exit(app.exec())
    except ImportError:
        print("[!] مكتبة PySide6 غير مثبتة في هذه البيئة. جاري التشغيل في وضع سطر الأوامر (CLI)...")
        print("[!] لتشغيل الواجهة الرسومية محلياً: pip install PySide6 ثم python main.py")
        run_cli_demo(args.db)


if __name__ == "__main__":
    main()
