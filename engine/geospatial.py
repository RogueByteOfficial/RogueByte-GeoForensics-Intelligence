"""
RogueByte GeoForensics Intelligence - Geospatial Evidence Engine
==============================================================
Encapsulates spatial coordinates, uncertainty radiuses, coordinate reference systems (CRS),
and geodesic calculations. Adheres strictly to the principle of never manufacturing coordinates
when only coarse regional or cell sector data is available.
"""

import math
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum


class LocationCategory(str, Enum):
    PHYSICAL_PERSON = "PHYSICAL_PERSON"         # Person's corroborated physical presence
    DEVICE_OBSERVED = "DEVICE_OBSERVED"         # Direct sensor/GPS from hardware artifact
    ACCOUNT_ACTIVITY = "ACCOUNT_ACTIVITY"       # Social media / web account session timestamp
    IP_NETWORK_ESTIMATE = "IP_NETWORK_ESTIMATE" # Coarse IP geolocation (City/ASN level only)
    CELLULAR_OBSERVATION = "CELLULAR_OBSERVATION" # Cell tower antenna sector / timing advance
    FILE_EMBEDDED_EXIF = "FILE_EMBEDDED_EXIF"   # EXIF GPS tag in image/video container
    WIFI_NETWORK_SCAN = "WIFI_NETWORK_SCAN"     # BSSID 802.11 beacon observation
    PROVIDER_AUTHORIZED = "PROVIDER_AUTHORIZED" # Official telco/platform subpoena record
    UNVERIFIED_HYPOTHESIS = "UNVERIFIED_HYPOTHESIS" # Analytical theory requiring corroboration


class LocationModality(str, Enum):
    DIRECT = "DIRECT"           # Directly recorded by high-precision sensor
    INFERRED = "INFERRED"       # Calculated from network topology or triangulation
    HISTORICAL = "HISTORICAL"   # Historical cached log or registration address
    UNVERIFIED = "UNVERIFIED"   # Claimed by user, uncorroborated text, or hypothesis


class GeoObservation:
    """Represents an atomic, immutable geographic observation backed by forensic evidence."""
    def __init__(
        self,
        observation_id: str,
        category: LocationCategory,
        modality: LocationModality,
        timestamp_iso: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        accuracy_radius_meters: Optional[float] = None,
        crs: str = "EPSG:4326",
        source_evidence_id: str = "",
        acquisition_method: str = "",
        reliability_notes: str = "",
        location_descriptor: str = "",
        cell_sector_details: Optional[Dict[str, Any]] = None,
        ip_metadata: Optional[Dict[str, Any]] = None,
    ):
        self.observation_id = observation_id
        self.category = category
        self.modality = modality
        self.timestamp_iso = timestamp_iso
        self.latitude = latitude
        self.longitude = longitude
        self.accuracy_radius_meters = accuracy_radius_meters
        self.crs = crs
        self.source_evidence_id = source_evidence_id
        self.acquisition_method = acquisition_method
        self.reliability_notes = reliability_notes
        self.location_descriptor = location_descriptor
        self.cell_sector_details = cell_sector_details or {}
        self.ip_metadata = ip_metadata or {}

        # Validation: Verify bounds if coordinates exist
        if self.latitude is not None:
            if not (-90.0 <= self.latitude <= 90.0):
                raise ValueError(f"Latitude out of bounds [-90, 90]: {self.latitude}")
        if self.longitude is not None:
            if not (-180.0 <= self.longitude <= 180.0):
                raise ValueError(f"Longitude out of bounds [-180, 180]: {self.longitude}")

    @property
    def has_point_coordinates(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "category": self.category.value,
            "modality": self.modality.value,
            "timestamp_iso": self.timestamp_iso,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "accuracy_radius_meters": self.accuracy_radius_meters,
            "crs": self.crs,
            "source_evidence_id": self.source_evidence_id,
            "acquisition_method": self.acquisition_method,
            "reliability_notes": self.reliability_notes,
            "location_descriptor": self.location_descriptor,
            "cell_sector_details": self.cell_sector_details,
            "ip_metadata": self.ip_metadata,
            "has_point_coordinates": self.has_point_coordinates
        }


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two points on the WGS-84 sphere in meters.
    """
    R = 6371000.0  # Earth's mean radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return R * c


def do_uncertainty_circles_overlap(
    obs1: GeoObservation, obs2: GeoObservation
) -> Tuple[bool, float, float]:
    """
    Determines if two spatial uncertainty circles intersect or overlap.
    Returns: (overlaps: bool, center_distance_meters: float, sum_of_radii_meters: float)
    """
    if not (obs1.has_point_coordinates and obs2.has_point_coordinates):
        return (False, -1.0, -1.0)

    dist = haversine_distance_meters(obs1.latitude, obs1.longitude, obs2.latitude, obs2.longitude)
    r1 = obs1.accuracy_radius_meters if obs1.accuracy_radius_meters is not None else 50.0
    r2 = obs2.accuracy_radius_meters if obs2.accuracy_radius_meters is not None else 50.0
    sum_r = r1 + r2

    return (dist <= sum_r, dist, sum_r)


def calculate_implausible_velocity(
    obs1: GeoObservation,
    obs2: GeoObservation,
    time1_iso: str,
    time2_iso: str,
    max_commercial_flight_speed_kmh: float = 950.0
) -> Dict[str, Any]:
    """
    Calculates velocity between two observations. If the implied speed exceeds
    commercial flight velocity, flags a physical impossibility (e.g. impossible simultaneous location).
    """
    from datetime import datetime, timezone

    if not (obs1.has_point_coordinates and obs2.has_point_coordinates):
        return {"plausible": True, "speed_kmh": 0.0, "reason": "No coordinates for comparison"}

    t1 = datetime.fromisoformat(time1_iso.replace('Z', '+00:00'))
    t2 = datetime.fromisoformat(time2_iso.replace('Z', '+00:00'))
    delta_sec = abs((t2 - t1).total_seconds())

    dist_meters = haversine_distance_meters(obs1.latitude, obs1.longitude, obs2.latitude, obs2.longitude)
    
    # Take uncertainty radius into account: minimum displacement
    r1 = obs1.accuracy_radius_meters or 0.0
    r2 = obs2.accuracy_radius_meters or 0.0
    min_dist_meters = max(0.0, dist_meters - (r1 + r2))

    if delta_sec < 1.0:
        if min_dist_meters > 500.0:
            return {
                "plausible": False,
                "speed_kmh": float('inf'),
                "displacement_km": dist_meters / 1000.0,
                "delta_seconds": delta_sec,
                "reason": f"Displacement of {dist_meters:.0f}m within <1 second (physically impossible for a single device)"
            }
        return {"plausible": True, "speed_kmh": 0.0, "reason": "Coincident in time and space"}

    speed_mps = min_dist_meters / delta_sec
    speed_kmh = speed_mps * 3.6

    is_plausible = speed_kmh <= max_commercial_flight_speed_kmh

    return {
        "plausible": is_plausible,
        "speed_kmh": round(speed_kmh, 2),
        "displacement_km": round(dist_meters / 1000.0, 3),
        "delta_seconds": round(delta_sec, 1),
        "reason": "Speed exceeds realistic human travel threshold" if not is_plausible else "Plausible physical trajectory"
    }
