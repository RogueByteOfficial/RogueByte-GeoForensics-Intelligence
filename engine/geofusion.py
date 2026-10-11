"""
RogueByte GeoForensics Intelligence - Temporal GeoFusion Engine
=============================================================
Core innovation: Correlates time-stamped digital evidence, geospatial observations,
device artifacts, network records, and authorized third-party records.
Provides explainable, court-defensible analysis without arbitrary confidence scores.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import math

from .geospatial import (
    GeoObservation,
    LocationCategory,
    LocationModality,
    haversine_distance_meters,
    do_uncertainty_circles_overlap,
    calculate_implausible_velocity
)
from .temporal import parse_timestamp, NormalizedTimestamp


class DefensibilityTier:
    CONCLUSIVE_CORROBORATED = "CONCLUSIVE_CORROBORATED"  # Multi-sensor independent overlap
    PROBABLE_SINGLE_SOURCE = "PROBABLE_SINGLE_SOURCE"    # High-quality sensor, no contradiction, but uncorroborated
    AMBIGUOUS_CONTRADICTORY = "AMBIGUOUS_CONTRADICTORY"  # Direct spatial contradiction exists (e.g. GPS vs IP vs Cell)
    COARSE_REGIONAL_ONLY = "COARSE_REGIONAL_ONLY"        # Only IP or regional cell data available; point location unknown
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"      # Sparse, out-of-window, or missing timestamps


class GeoFusionResult:
    """The defensible result of the Temporal GeoFusion Engine."""
    def __init__(
        self,
        incident_time_iso: str,
        defensibility_tier: str,
        defensible_summary: str,
        primary_estimate_coordinates: Optional[Tuple[float, float]],
        estimated_accuracy_radius_meters: Optional[float],
        corroborating_evidence_ids: List[str],
        contradictory_evidence_ids: List[str],
        unresolved_hypotheses: List[str],
        limitations: List[str],
        detailed_calculations: List[Dict[str, Any]],
        evidence_evaluations: List[Dict[str, Any]],
    ):
        self.incident_time_iso = incident_time_iso
        self.defensibility_tier = defensibility_tier
        self.defensible_summary = defensible_summary
        self.primary_estimate_coordinates = primary_estimate_coordinates
        self.estimated_accuracy_radius_meters = estimated_accuracy_radius_meters
        self.corroborating_evidence_ids = corroborating_evidence_ids
        self.contradictory_evidence_ids = contradictory_evidence_ids
        self.unresolved_hypotheses = unresolved_hypotheses
        self.limitations = limitations
        self.detailed_calculations = detailed_calculations
        self.evidence_evaluations = evidence_evaluations

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_time_iso": self.incident_time_iso,
            "defensibility_tier": self.defensibility_tier,
            "defensible_summary": self.defensible_summary,
            "primary_estimate_coordinates": self.primary_estimate_coordinates,
            "estimated_accuracy_radius_meters": self.estimated_accuracy_radius_meters,
            "corroborating_evidence_ids": self.corroborating_evidence_ids,
            "contradictory_evidence_ids": self.contradictory_evidence_ids,
            "unresolved_hypotheses": self.unresolved_hypotheses,
            "limitations": self.limitations,
            "detailed_calculations": self.detailed_calculations,
            "evidence_evaluations": self.evidence_evaluations,
        }


class TemporalGeoFusionEngine:
    """
    Executes the explainable evidence-correlation algorithm.
    Adheres strictly to forensic methodology:
    - Never equates IP location with physical human presence.
    - Employs strict distance and uncertainty tolerance.
    - Flags impossible velocities (e.g. displacement between simultaneous records).
    """

    def __init__(
        self,
        temporal_window_seconds: float = 1800.0,  # default +/- 30 minutes
        max_human_velocity_kmh: float = 950.0
    ):
        self.temporal_window_seconds = temporal_window_seconds
        self.max_human_velocity_kmh = max_human_velocity_kmh

    def fuse(
        self,
        incident_time_iso: str,
        observations: List[GeoObservation],
        case_target_account: Optional[str] = None
    ) -> GeoFusionResult:
        inc_ts = parse_timestamp(incident_time_iso)
        inc_dt = inc_ts.utc_dt

        calculations: List[Dict[str, Any]] = []
        evaluations: List[Dict[str, Any]] = []
        corroborated: List[str] = []
        contradicted: List[str] = []
        hypotheses: List[str] = []
        limitations: List[str] = []

        if not observations:
            return GeoFusionResult(
                incident_time_iso=incident_time_iso,
                defensibility_tier=DefensibilityTier.INSUFFICIENT_EVIDENCE,
                defensible_summary="لا تتوفر أي ملاحظات أو أدلة جغرافية مسجلة للواقعة. الأدلة غير كافية قطعاً.",
                primary_estimate_coordinates=None,
                estimated_accuracy_radius_meters=None,
                corroborating_evidence_ids=[],
                contradictory_evidence_ids=[],
                unresolved_hypotheses=["لم يتم تقديم أي سجلات اتصالات أو إحداثيات أو سجلات عناوين IP."],
                limitations=["غياب تام لأي أدلة رقمية مساندة."],
                detailed_calculations=[],
                evidence_evaluations=[]
            )

        # 1. Filter observations within temporal window (accounting for timestamp uncertainty)
        in_window_obs: List[Tuple[GeoObservation, float]] = []
        for obs in observations:
            obs_ts = parse_timestamp(obs.timestamp_iso)
            delta_sec = (obs_ts.utc_dt - inc_dt).total_seconds()
            abs_delta = abs(delta_sec)
            
            # Check effective window with uncertainty tolerance
            is_in_window = abs_delta <= (self.temporal_window_seconds + obs_ts.uncertainty_seconds)

            eval_entry = {
                "observation_id": obs.observation_id,
                "category": obs.category.value,
                "modality": obs.modality.value,
                "time_delta_seconds": round(delta_sec, 1),
                "in_window": is_in_window,
                "coordinates": (obs.latitude, obs.longitude) if obs.has_point_coordinates else None,
                "accuracy_radius_meters": obs.accuracy_radius_meters,
                "notes": obs.reliability_notes
            }
            evaluations.append(eval_entry)

            if is_in_window:
                in_window_obs.append((obs, abs_delta))

        if not in_window_obs:
            return GeoFusionResult(
                incident_time_iso=incident_time_iso,
                defensibility_tier=DefensibilityTier.INSUFFICIENT_EVIDENCE,
                defensible_summary="توجد أدلة جغرافية خارج النافذة الزمنية المحددة للواقعة، ولكن لا توجد أي أدلة متزامنة مع وقت الحدث.",
                primary_estimate_coordinates=None,
                estimated_accuracy_radius_meters=None,
                corroborating_evidence_ids=[],
                contradictory_evidence_ids=[],
                unresolved_hypotheses=["قد تكون الأدلة التاريخية تشير إلى موقع سابق أو لاحق للهدف."],
                limitations=[f"النافذة الزمنية المطبقة هي +/- {self.temporal_window_seconds / 60:.0f} دقيقة."],
                detailed_calculations=[],
                evidence_evaluations=evaluations
            )

        # 2. Categorize observations
        device_gps = [o for o, _ in in_window_obs if o.category == LocationCategory.DEVICE_OBSERVED and o.has_point_coordinates]
        cell_obs = [o for o, _ in in_window_obs if o.category == LocationCategory.CELLULAR_OBSERVATION and o.has_point_coordinates]
        exif_obs = [o for o, _ in in_window_obs if o.category == LocationCategory.FILE_EMBEDDED_EXIF and o.has_point_coordinates]
        wifi_obs = [o for o, _ in in_window_obs if o.category == LocationCategory.WIFI_NETWORK_SCAN and o.has_point_coordinates]
        provider_obs = [o for o, _ in in_window_obs if o.category == LocationCategory.PROVIDER_AUTHORIZED and o.has_point_coordinates]
        ip_obs = [o for o, _ in in_window_obs if o.category == LocationCategory.IP_NETWORK_ESTIMATE]

        all_point_obs = [o for o, _ in in_window_obs if o.has_point_coordinates]

        # 3. Detect Contradictions & Velocity Implausibilities
        contradictions_found = False
        pairwise_calc: List[Dict[str, Any]] = []

        for i in range(len(all_point_obs)):
            for j in range(i + 1, len(all_point_obs)):
                o1 = all_point_obs[i]
                o2 = all_point_obs[j]

                overlaps, dist, sum_r = do_uncertainty_circles_overlap(o1, o2)
                vel_res = calculate_implausible_velocity(
                    o1, o2, o1.timestamp_iso, o2.timestamp_iso, self.max_human_velocity_kmh
                )

                calc_rec = {
                    "pair": (o1.observation_id, o2.observation_id),
                    "categories": (o1.category.value, o2.category.value),
                    "distance_meters": round(dist, 1),
                    "combined_uncertainty_radius_meters": round(sum_r, 1),
                    "spatial_overlap": overlaps,
                    "velocity_analysis": vel_res
                }
                pairwise_calc.append(calc_rec)

                # Flag contradiction:
                # If both are physical/device/cell observations and uncertainty circles do NOT overlap
                # OR velocity is physically impossible between contemporaneous events
                if not vel_res["plausible"]:
                    contradictions_found = True
                    contradicted.extend([o1.observation_id, o2.observation_id])
                    calc_rec["finding"] = "CONTRADICTION: Impossible velocity between events."
                elif not overlaps:
                    # If an IP network location differs from device GPS, explain the distinction
                    if o1.category == LocationCategory.IP_NETWORK_ESTIMATE or o2.category == LocationCategory.IP_NETWORK_ESTIMATE:
                        calc_rec["finding"] = "IP_DISCREPANCY: Coarse IP network geolocation differs from sensor coordinates (expected behavior with VPN/Carrier NAT)."
                    else:
                        contradictions_found = True
                        contradicted.extend([o1.observation_id, o2.observation_id])
                        calc_rec["finding"] = "SPATIAL_CONFLICT: Non-overlapping uncertainty zones between device sensors/cells."

        calculations.extend(pairwise_calc)
        contradicted = list(set(contradicted))

        # 4. Formulate Defensible Conclusion
        # Priority 1: High-precision verified device GPS or Provider CDR corroborated by Cell/WiFi
        primary_coords: Optional[Tuple[float, float]] = None
        accuracy_radius: Optional[float] = None
        tier = DefensibilityTier.INSUFFICIENT_EVIDENCE
        summary = ""

        if contradictions_found:
            tier = DefensibilityTier.AMBIGUOUS_CONTRADICTORY
            summary = (
                "تم رصد تناقض مكاني أو سرعة انتقال مستحيلة فيزيائياً بين الأدلة المرصودة. "
                "يشير هذا إما إلى استخدام أجهزة متعددة لنفس الحساب بالتزامن، أو تزييف إحداثيات (GPS Spoofing)، "
                "أو وجود خادم وكيل (VPN/Proxy)، أو تفاوت في توقيت ساعات الأجهزة."
            )
            hypotheses.append("الفرضية أ: استخدام جهازين مختلفين (مثل هاتف وحاسوب محمول عبر VPN).")
            hypotheses.append("الفرضية ب: تزييف موقع GPS برمجياً على جهاز الهدف.")
            hypotheses.append("الفرضية ج: خطأ في مزامنة توقيت أحد السجلات الأصلية (Clock Drift).")
            limitations.append("لا يمكن الجزم بموقع موحد دون الحصول على سجلات مزود الخدمة الموثقة بسجلات الجلسات الصريحة (Radius Logs).")

        elif (device_gps or provider_obs) and (cell_obs or wifi_obs or exif_obs):
            # True multi-sensor corroboration
            corroborating_source = device_gps[0] if device_gps else provider_obs[0]
            primary_coords = (corroborating_source.latitude, corroborating_source.longitude)
            accuracy_radius = corroborating_source.accuracy_radius_meters or 30.0
            tier = DefensibilityTier.CONCLUSIVE_CORROBORATED
            corroborated = [o.observation_id for o, _ in in_window_obs if o.has_point_coordinates]

            summary = (
                f"تطابق متعدد المصادر ومؤكد جنائياً: تقاطع إحداثيات الجهاز المباشرة مع برج الاتصالات/الشبكة بنصف قطر دقة {accuracy_radius:.0f}متر. "
                "الاستنتاج مدعوم بأدلة مستقلة متزامنة زمنياً."
            )
            limitations.append("دقة الموقع مرتبطة بمستشعر الجهاز ودقة قطاع البرج الخلوي.")

        elif device_gps or provider_obs:
            # Single high-quality source without independent physical corroboration
            target = device_gps[0] if device_gps else provider_obs[0]
            primary_coords = (target.latitude, target.longitude)
            accuracy_radius = target.accuracy_radius_meters or 50.0
            tier = DefensibilityTier.PROBABLE_SINGLE_SOURCE
            corroborated = [target.observation_id]

            summary = (
                f"تم تحديد موقع الجهاز استناداً إلى مصدر موثوق منفرد ({target.category.value}) "
                f"بدقة تقديرية {accuracy_radius:.0f}متر، مع غياب تأكيد مستقل من أبراج الاتصالات في ذات اللحظة."
            )
            hypotheses.append("الموقع مسجل من الجهاز مباشرة؛ يتطلب تعزيزاً بطلب سجلات برج الاتصالات (Cell CDR).")
            limitations.append("لم يتم العثور على سجلات أبراج خلوية مستقلة في نفس الدقيقة لتأكيد عدم وجود تزييف GPS.")

        elif cell_obs:
            # Cellular sector only
            c = cell_obs[0]
            primary_coords = (c.latitude, c.longitude)
            accuracy_radius = c.accuracy_radius_meters or 1500.0
            tier = DefensibilityTier.COARSE_REGIONAL_ONLY
            corroborated = [c.observation_id]
            summary = (
                f"الموقع محدد ضمن قطاع تغطية برج الاتصالات بنصف قطر {accuracy_radius / 1000.0:.1f} كم. "
                "لا يجوز قانونياً أو فنياً اختلاق إحداثيات نقطية محددة للهدف داخل هذا النطاق."
            )
            limitations.append("سجلات البرج تحدد قطاع التغطية فقط ولا تمثل موقع الشخص بدقة GPS.")

        elif ip_obs:
            # Only coarse IP data
            tier = DefensibilityTier.COARSE_REGIONAL_ONLY
            summary = (
                "الأدلة المتاحة تقتصر على عنوان IP للشبكة فقط. "
                "من الناحية الجنائية، عنوان IP يعكس مركز بيانات مزود الخدمة أو نقطة توجيه ولا يثبت الوجود الفيزيائي للشخص."
            )
            hypotheses.append("قد يكون الاتصال تم عبر شبكة خاصة افتراضية (VPN) أو NAT لمزود الخدمة.")
            limitations.append("عنوان IP لا يمثل موقعاً جغرافياً نهائياً ويحتاج إذن قضائي لطلب سجلات المشترك (ISP Subscriber Data).")

        return GeoFusionResult(
            incident_time_iso=incident_time_iso,
            defensibility_tier=tier,
            defensible_summary=summary,
            primary_estimate_coordinates=primary_coords,
            estimated_accuracy_radius_meters=accuracy_radius,
            corroborating_evidence_ids=corroborated,
            contradictory_evidence_ids=contradicted,
            unresolved_hypotheses=hypotheses,
            limitations=limitations,
            detailed_calculations=calculations,
            evidence_evaluations=evaluations,
        )
