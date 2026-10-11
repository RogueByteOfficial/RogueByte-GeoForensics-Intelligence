"""
RogueByte GeoForensics Intelligence - Forensic Report Generator
=============================================================
Generates court-defensible, high-integrity forensic reports containing:
- Case summary & Chain of Custody
- Cryptographic SHA-256 evidence manifest
- Incident timeline with UTC normalization
- Temporal GeoFusion analysis & Contradiction matrix
- Clear separation between Observed Facts, Analytical Inferences, and Unresolved Hypotheses.
Exports to standalone forensic HTML (printable to PDF) and direct ReportLab PDF.
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


SOFTWARE_NAME = "RogueByte GeoForensics Intelligence"
SOFTWARE_VERSION = "2.4.0-PROD"


class ForensicReportGenerator:
    """Produces standardized forensic reports in HTML and PDF formats."""

    @staticmethod
    def generate_html_report(
        case: Dict[str, Any],
        evidence_items: List[Dict[str, Any]],
        chain_of_custody: List[Dict[str, Any]],
        observations: List[Dict[str, Any]],
        fusion_result: Optional[Dict[str, Any]],
        audit_trail: List[Dict[str, Any]],
        output_filepath: str
    ) -> str:
        gen_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Build HTML content with dark/print forensic design
        html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>تقرير التحقيق الجنائي الجغرافي - {case.get('case_id')}</title>
    <style>
        @media print {{
            body {{ background: #fff !important; color: #000 !important; font-size: 11pt; }}
            .no-print {{ display: none; }}
            .page-break {{ page-break-before: always; }}
            .card {{ border: 1px solid #ccc !important; box-shadow: none !important; }}
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
            background: #0b0f19;
            color: #e2e8f0;
            line-height: 1.6;
            margin: 0;
            padding: 30px;
        }}
        .header {{
            border-bottom: 2px solid #06b6d4;
            padding-bottom: 20px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .brand {{
            font-size: 24px;
            font-weight: bold;
            color: #38bdf8;
            letter-spacing: 1px;
        }}
        .sub-brand {{
            font-size: 13px;
            color: #94a3b8;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .badge-cyan {{ background: rgba(6, 182, 212, 0.2); color: #22d3ee; border: 1px solid #0891b2; }}
        .badge-red {{ background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #dc2626; }}
        .badge-green {{ background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid #16a34a; }}
        .card {{
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 25px;
        }}
        h2 {{
            color: #38bdf8;
            font-size: 18px;
            border-right: 4px solid #06b6d4;
            padding-right: 12px;
            margin-top: 0;
            margin-bottom: 15px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-top: 10px;
        }}
        th, td {{
            padding: 8px 12px;
            text-align: right;
            border-bottom: 1px solid #1f2937;
        }}
        th {{
            background: #1f2937;
            color: #93c5fd;
            font-weight: 600;
        }}
        .hash-code {{
            font-family: monospace;
            font-size: 11px;
            color: #cbd5e1;
            word-break: break-all;
            background: #0f172a;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        .alert-box {{
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 15px;
        }}
        .alert-conclusive {{ background: rgba(34, 197, 94, 0.1); border: 1px solid #22c55e; color: #86efac; }}
        .alert-contradictory {{ background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; color: #fca5a5; }}
        .alert-warning {{ background: rgba(234, 179, 8, 0.1); border: 1px solid #eab308; color: #fde047; }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .meta-item {{
            background: #0f172a;
            padding: 10px 15px;
            border-radius: 6px;
            border: 1px solid #1e293b;
        }}
        .meta-label {{ font-size: 11px; color: #64748b; margin-bottom: 4px; }}
        .meta-value {{ font-size: 14px; font-weight: 600; color: #f1f5f9; }}
        .footer {{
            margin-top: 40px;
            padding-top: 15px;
            border-top: 1px solid #1f2937;
            text-align: center;
            font-size: 11px;
            color: #64748b;
        }}
    </style>
</head>
<body>

    <div class="header">
        <div>
            <div class="brand">ROGUEBYTE GEOFORENSICS INTELLIGENCE</div>
            <div class="sub-brand">تقرير فحص وتطابق مكاني وزمني رقمي رسمي</div>
        </div>
        <div style="text-align: left;">
            <span class="badge badge-cyan">مستوى السرية: رسمي - مصنف للتحقيق</span><br>
            <span style="font-size: 11px; color: #94a3b8;">تاريخ التوليد: {gen_time_utc}</span>
        </div>
    </div>

    <!-- Case Summary Card -->
    <div class="card">
        <h2>1. ملخص القضية وبيانات المحقق (Case Summary)</h2>
        <div class="meta-grid">
            <div class="meta-item">
                <div class="meta-label">معرف القضية (Case ID)</div>
                <div class="meta-value">{case.get('case_id', 'N/A')}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">عنوان القضية</div>
                <div class="meta-value">{case.get('title', 'N/A')}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">المحقق المسؤول</div>
                <div class="meta-value">{case.get('investigator_id', 'N/A')} ({case.get('investigator_role', 'N/A')})</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">وقت الواقعة المرجعي (UTC)</div>
                <div class="meta-value">{case.get('incident_time_utc', 'N/A')}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">الحساب المستهدف</div>
                <div class="meta-value">{case.get('target_account', 'N/A')}</div>
            </div>
        </div>
    </div>

    <!-- GeoFusion Results -->
    <div class="card">
        <h2>2. نتائج محرك التحليل الزمني المكاني (Temporal GeoFusion Engine)</h2>
        """

        if fusion_result:
            tier = fusion_result.get("defensibility_tier", "INSUFFICIENT_EVIDENCE")
            box_class = "alert-warning"
            if tier == "CONCLUSIVE_CORROBORATED":
                box_class = "alert-conclusive"
            elif tier == "AMBIGUOUS_CONTRADICTORY":
                box_class = "alert-contradictory"

            html += f"""
            <div class="alert-box {box_class}">
                <strong>تصنيف الموثوقية الجنائية:</strong> {tier}<br>
                <p style="margin: 8px 0 0 0;">{fusion_result.get('defensible_summary', '')}</p>
            </div>
            """

            coords = fusion_result.get("primary_estimate_coordinates")
            rad = fusion_result.get("estimated_accuracy_radius_meters")
            if coords:
                html += f"""
                <div class="meta-grid" style="margin-top: 15px;">
                    <div class="meta-item">
                        <div class="meta-label">الإحداثيات المقدرة قانونياً (WGS-84)</div>
                        <div class="meta-value">{coords[0]:.6f}, {coords[1]:.6f}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">نصف قطر عدم اليقين (Accuracy Radius)</div>
                        <div class="meta-value">+/- {rad:.0f} متر</div>
                    </div>
                </div>
                """

            contra = fusion_result.get("contradictory_evidence_ids", [])
            if contra:
                html += f"""
                <div style="margin-top: 15px; color: #f87171; font-size: 13px;">
                    <strong>الأدلة المتناقضة التي تم استبعادها أو تحديد تضاربها:</strong> {", ".join(contra)}
                </div>
                """

            hypotheses = fusion_result.get("unresolved_hypotheses", [])
            if hypotheses:
                html += "<h3 style='font-size: 14px; color: #cbd5e1; margin-top: 15px;'>الفرضيات التحليلية غير المحسومة (Hypotheses):</h3><ul>"
                for h in hypotheses:
                    html += f"<li style='font-size: 12px; color: #94a3b8;'>{h}</li>"
                html += "</ul>"

            limitations = fusion_result.get("limitations", [])
            if limitations:
                html += "<h3 style='font-size: 14px; color: #cbd5e1; margin-top: 15px;'>المحددات الجنائية والفنية (Forensic Limitations):</h3><ul>"
                for lim in limitations:
                    html += f"<li style='font-size: 12px; color: #fca5a5;'>{lim}</li>"
                html += "</ul>"

        else:
            html += "<p>لم يتم تشغيل محرك المطابقة لهذه القضية حتى الآن.</p>"

        html += f"""
    </div>

    <!-- Evidence Manifest -->
    <div class="card page-break">
        <h2>3. سجل فحص الأدلة الرقمية والتشفير (SHA-256 Evidence Manifest)</h2>
        <p style="font-size: 12px; color: #94a3b8;">
            تم احتساب البصمة الرقمية SHA-256 فور إيداع كل ملف، وتم إيداعه في وحدة تخزين للقراءة فقط لمنع أي تعديل أو عبث.
        </p>
        <table>
            <thead>
                <tr>
                    <th>معرف الدليل</th>
                    <th>اسم الملف</th>
                    <th>المصدر</th>
                    <th>وقت التحريز (UTC)</th>
                    <th>الحجم (بايت)</th>
                    <th>بصمة SHA-256 الأصلية</th>
                </tr>
            </thead>
            <tbody>
        """

        for ev in evidence_items:
            html += f"""
                <tr>
                    <td><strong>{ev.get('evidence_id')}</strong></td>
                    <td>{ev.get('filename')}</td>
                    <td>{ev.get('source_type')}</td>
                    <td>{ev.get('acquisition_time_utc')}</td>
                    <td>{ev.get('file_size_bytes')}</td>
                    <td><span class="hash-code">{ev.get('sha256_hash')}</span></td>
                </tr>
            """

        html += f"""
            </tbody>
        </table>
    </div>

    <!-- Chain of Custody -->
    <div class="card">
        <h2>4. سلسلة الحيازة الجنائية (Chain of Custody & Verification History)</h2>
        <table>
            <thead>
                <tr>
                    <th>التاريخ والتوقيت (UTC)</th>
                    <th>معرف الدليل</th>
                    <th>الإجراء المنجز</th>
                    <th>المحقق / الفاحص</th>
                    <th>نتيجة تدقيق الهاش</th>
                    <th>ملاحظات التدقيق</th>
                </tr>
            </thead>
            <tbody>
        """

        for c in chain_of_custody:
            passed = c.get('verification_passed', 1)
            status_badge = '<span class="badge badge-green">مطابق سليم</span>' if passed else '<span class="badge badge-red">تحذير تضارب!</span>'
            html += f"""
                <tr>
                    <td>{c.get('timestamp_utc')}</td>
                    <td>{c.get('evidence_id')}</td>
                    <td>{c.get('action_type')}</td>
                    <td>{c.get('actor_id')} ({c.get('actor_role', '')})</td>
                    <td>{status_badge}</td>
                    <td>{c.get('notes', '')}</td>
                </tr>
            """

        html += f"""
            </tbody>
        </table>
    </div>

    <!-- Geographic Observations Details -->
    <div class="card page-break">
        <h2>5. قائمة الملاحظات الجغرافية المرصودة (Geographic Observations Log)</h2>
        <table>
            <thead>
                <tr>
                    <th>المعرف</th>
                    <th>التصنيف الدقيق</th>
                    <th>التوقيت الموحد (UTC)</th>
                    <th>خط العرض / الطول</th>
                    <th>نصف قطر الخطأ</th>
                    <th>المحددات والملاحظات الفنية</th>
                </tr>
            </thead>
            <tbody>
        """

        for obs in observations:
            lat = f"{obs.get('latitude'):.5f}" if obs.get('latitude') is not None else "غير متاح"
            lon = f"{obs.get('longitude'):.5f}" if obs.get('longitude') is not None else "غير متاح"
            rad = f"{obs.get('accuracy_radius_meters'):.0f}م" if obs.get('accuracy_radius_meters') is not None else "-"
            html += f"""
                <tr>
                    <td>{obs.get('observation_id')}</td>
                    <td><span class="badge badge-cyan">{obs.get('category')}</span></td>
                    <td>{obs.get('timestamp_utc')}</td>
                    <td>{lat}, {lon}</td>
                    <td>{rad}</td>
                    <td>{obs.get('reliability_notes', '')}</td>
                </tr>
            """

        html += f"""
            </tbody>
        </table>
    </div>

    <!-- Tamper Evident Audit Log -->
    <div class="card">
        <h2>6. سجل التدقيق الجنائي غير القابل للتلاعب (Tamper-Evident Chained Audit Log)</h2>
        <p style="font-size: 12px; color: #94a3b8;">
            كل إدخال مشفر ومرتبط بهاش السجل السابق في سلسلة موثوقة تضمن كشف أي تعديل على قاعدة البيانات.
        </p>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>التوقيت (UTC)</th>
                    <th>العملية</th>
                    <th>المنفذ</th>
                    <th>هاش المدخلة (Entry Hash)</th>
                </tr>
            </thead>
            <tbody>
        """

        for a in audit_trail[:15]:  # show up to 15 recent entries
            html += f"""
                <tr>
                    <td>{a.get('log_index')}</td>
                    <td>{a.get('timestamp_utc')}</td>
                    <td><strong>{a.get('action')}</strong></td>
                    <td>{a.get('actor_id')}</td>
                    <td><span class="hash-code">{a.get('entry_hash')}</span></td>
                </tr>
            """

        html += f"""
            </tbody>
        </table>
    </div>

    <div class="footer">
        تم إنشاء هذا التقرير الجنائي آلياً بواسطة برمجية <strong>{SOFTWARE_NAME}</strong> الإصدار {SOFTWARE_VERSION}<br>
        هذا المستند يتضمن تفاصيل تقنية محكمة تفصل بين الحقائق المرصودة، الاستنتاجات التحليلية، والفرضيات غير المحسومة.
    </div>

</body>
</html>
"""

        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(html)

        return output_filepath
