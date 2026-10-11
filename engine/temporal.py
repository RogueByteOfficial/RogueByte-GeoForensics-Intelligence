"""
RogueByte GeoForensics Intelligence - Temporal Evidence Engine
=============================================================
Handles UTC normalization, clock drift detection, timestamp uncertainty intervals,
and impossible event sequence detection.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any, List
import re
import math


class NormalizedTimestamp:
    """Represents a normalized timestamp in UTC while preserving original provenance."""
    def __init__(
        self,
        utc_dt: datetime,
        original_repr: str,
        timezone_offset_minutes: int = 0,
        uncertainty_seconds: float = 0.0,
        precision: str = "second"
    ):
        if utc_dt.tzinfo is None:
            self.utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        else:
            self.utc_dt = utc_dt.astimezone(timezone.utc)
            
        self.original_repr = str(original_repr)
        self.timezone_offset_minutes = int(timezone_offset_minutes)
        self.uncertainty_seconds = float(uncertainty_seconds)
        self.precision = precision

    @property
    def iso_utc(self) -> str:
        return self.utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    @property
    def window(self) -> Tuple[datetime, datetime]:
        """Returns the [earliest, latest] probable occurrence window considering uncertainty."""
        delta = timedelta(seconds=self.uncertainty_seconds)
        return (self.utc_dt - delta, self.utc_dt + delta)

    def to_dict(self) -> Dict[str, Any]:
        earliest, latest = self.window
        return {
            "utc_iso": self.iso_utc,
            "original_repr": self.original_repr,
            "tz_offset_minutes": self.timezone_offset_minutes,
            "uncertainty_seconds": self.uncertainty_seconds,
            "precision": self.precision,
            "window_start": earliest.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "window_end": latest.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }


def parse_timestamp(value: Any, default_uncertainty: float = 0.0) -> NormalizedTimestamp:
    """
    Parses various timestamp representations (ISO 8601, Epoch seconds/millis, SQL formats)
    into a NormalizedTimestamp without silently changing original semantics.
    """
    if isinstance(value, NormalizedTimestamp):
        return value

    original_repr = str(value).strip()
    
    # 1. Numeric Epoch
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '', 1).isdigit()):
        num = float(value)
        # Check milliseconds vs seconds
        if num > 1e11:  # milliseconds
            dt = datetime.fromtimestamp(num / 1000.0, tz=timezone.utc)
            precision = "millisecond"
        else:
            dt = datetime.fromtimestamp(num, tz=timezone.utc)
            precision = "second"
        return NormalizedTimestamp(dt, original_repr, 0, default_uncertainty, precision)

    # 2. ISO 8601 strings
    # Common format: 2026-10-11T15:30:00Z or with offset +03:00
    iso_clean = original_repr.replace(" ", "T")
    
    # Match timezone offset
    tz_match = re.search(r'([+-])(\d{2}):?(\d{2})?$', iso_clean)
    tz_offset_mins = 0
    if tz_match:
        sign = 1 if tz_match.group(1) == '+' else -1
        hours = int(tz_match.group(2))
        mins = int(tz_match.group(3)) if tz_match.group(3) else 0
        tz_offset_mins = sign * (hours * 60 + mins)

    # Replace 'Z' with +00:00 for fromisoformat
    if iso_clean.endswith("Z"):
        iso_clean = iso_clean[:-1] + "+00:00"
        
    try:
        dt = datetime.fromisoformat(iso_clean)
        if dt.tzinfo is None:
            # Assume UTC if not specified, but note zero offset
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return NormalizedTimestamp(dt, original_repr, tz_offset_mins, default_uncertainty, "second")
    except Exception:
        pass

    # Fallback standard formats
    formats = [
        ("%Y-%m-%d %H:%M:%S", 0, "second"),
        ("%Y-%m-%d %H:%M:%S.%f", 0, "millisecond"),
        ("%Y/%m/%d %H:%M:%S", 0, "second"),
        ("%d/%m/%Y %H:%M:%S", 0, "second"),
        ("%Y-%m-%d", 0, "date_only"),
    ]
    for fmt, offset, prec in formats:
        try:
            parsed = datetime.strptime(original_repr, fmt)
            parsed = parsed.replace(tzinfo=timezone.utc)
            return NormalizedTimestamp(parsed, original_repr, offset, default_uncertainty, prec)
        except ValueError:
            continue

    raise ValueError(f"Unrecognized timestamp format for evidence: '{original_repr}'")


def temporal_overlap(t1_window: Tuple[datetime, datetime], t2_window: Tuple[datetime, datetime]) -> bool:
    """Returns True if two time uncertainty intervals overlap."""
    return max(t1_window[0], t2_window[0]) <= min(t1_window[1], t2_window[1])


def temporal_distance_seconds(t1: NormalizedTimestamp, t2: NormalizedTimestamp) -> float:
    """Calculates absolute temporal delta in seconds between center points."""
    return abs((t1.utc_dt - t2.utc_dt).total_seconds())
