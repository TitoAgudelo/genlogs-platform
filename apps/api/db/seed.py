"""Seed the database with realistic pipeline data. Idempotent: skips if data exists."""

from db.database import Base, engine, SessionLocal
from db.models import (
    Camera,
    Carrier,
    ImageProcessingResult,
    ImageTransaction,
    Trip,
    Truck,
    TruckSighting,
)

# Fallback carriers for routes not in the database
FALLBACK_CARRIERS = [
    {"carrier_name": "UPS Inc.", "trucks_per_day": 11},
    {"carrier_name": "FedEx Corp", "trucks_per_day": 9},
]

# ---------------------------------------------------------------------------
# Cameras on major US highways
# ---------------------------------------------------------------------------
CAMERAS = [
    ("cam-001", 40.7580, -73.9855, "I-95 New York"),
    ("cam-002", 40.7214, -74.0052, "I-95 New York South"),
    ("cam-003", 38.9072, -77.0369, "I-95 Washington DC"),
    ("cam-004", 38.8816, -77.0910, "I-395 Washington DC"),
    ("cam-005", 37.7749, -122.4194, "US-101 San Francisco"),
    ("cam-006", 37.3382, -121.8863, "US-101 San Jose"),
    ("cam-007", 34.0522, -118.2437, "I-5 Los Angeles"),
    ("cam-008", 33.9425, -118.4081, "I-405 Los Angeles"),
]

# ---------------------------------------------------------------------------
# Carriers
# ---------------------------------------------------------------------------
CARRIERS = [
    ("carrier-001", "Knight-Swift Transport Services", "USDOT-2247642", "Phoenix"),
    ("carrier-002", "J.B. Hunt Transport Services Inc", "USDOT-655025", "Lowell"),
    ("carrier-003", "YRC Worldwide", "USDOT-1432024", "Overland Park"),
    ("carrier-004", "XPO Logistics", "USDOT-2211808", "Greenwich"),
    ("carrier-005", "Schneider", "USDOT-609tried", "Green Bay"),
    ("carrier-006", "Landstar Systems", "USDOT-1028580", "Jacksonville"),
    ("carrier-007", "UPS Inc.", "USDOT-2328610", "Atlanta"),
    ("carrier-008", "FedEx Corp", "USDOT-680937", "Memphis"),
]

# ---------------------------------------------------------------------------
# Trucks (license_plate, usdot, carrier_id)
# ---------------------------------------------------------------------------
TRUCKS = [
    # Knight-Swift — 10 trucks on NY→DC route
    ("trk-001", "NY-KS-1001", "USDOT-2247642", "carrier-001"),
    ("trk-002", "NY-KS-1002", "USDOT-2247642", "carrier-001"),
    ("trk-003", "NY-KS-1003", "USDOT-2247642", "carrier-001"),
    ("trk-004", "NY-KS-1004", "USDOT-2247642", "carrier-001"),
    ("trk-005", "NY-KS-1005", "USDOT-2247642", "carrier-001"),
    ("trk-006", "NY-KS-1006", "USDOT-2247642", "carrier-001"),
    ("trk-007", "NY-KS-1007", "USDOT-2247642", "carrier-001"),
    ("trk-008", "NY-KS-1008", "USDOT-2247642", "carrier-001"),
    ("trk-009", "NY-KS-1009", "USDOT-2247642", "carrier-001"),
    ("trk-010", "NY-KS-1010", "USDOT-2247642", "carrier-001"),
    # J.B. Hunt — 7 trucks on NY→DC route
    ("trk-011", "NY-JB-2001", "USDOT-655025", "carrier-002"),
    ("trk-012", "NY-JB-2002", "USDOT-655025", "carrier-002"),
    ("trk-013", "NY-JB-2003", "USDOT-655025", "carrier-002"),
    ("trk-014", "NY-JB-2004", "USDOT-655025", "carrier-002"),
    ("trk-015", "NY-JB-2005", "USDOT-655025", "carrier-002"),
    ("trk-016", "NY-JB-2006", "USDOT-655025", "carrier-002"),
    ("trk-017", "NY-JB-2007", "USDOT-655025", "carrier-002"),
    # YRC Worldwide — 5 trucks on NY→DC route
    ("trk-018", "NY-YR-3001", "USDOT-1432024", "carrier-003"),
    ("trk-019", "NY-YR-3002", "USDOT-1432024", "carrier-003"),
    ("trk-020", "NY-YR-3003", "USDOT-1432024", "carrier-003"),
    ("trk-021", "NY-YR-3004", "USDOT-1432024", "carrier-003"),
    ("trk-022", "NY-YR-3005", "USDOT-1432024", "carrier-003"),
    # XPO Logistics — 9 trucks on SF→LA route
    ("trk-023", "CA-XP-4001", "USDOT-2211808", "carrier-004"),
    ("trk-024", "CA-XP-4002", "USDOT-2211808", "carrier-004"),
    ("trk-025", "CA-XP-4003", "USDOT-2211808", "carrier-004"),
    ("trk-026", "CA-XP-4004", "USDOT-2211808", "carrier-004"),
    ("trk-027", "CA-XP-4005", "USDOT-2211808", "carrier-004"),
    ("trk-028", "CA-XP-4006", "USDOT-2211808", "carrier-004"),
    ("trk-029", "CA-XP-4007", "USDOT-2211808", "carrier-004"),
    ("trk-030", "CA-XP-4008", "USDOT-2211808", "carrier-004"),
    ("trk-031", "CA-XP-4009", "USDOT-2211808", "carrier-004"),
    # Schneider — 6 trucks on SF→LA route
    ("trk-032", "CA-SN-5001", "USDOT-609tried", "carrier-005"),
    ("trk-033", "CA-SN-5002", "USDOT-609tried", "carrier-005"),
    ("trk-034", "CA-SN-5003", "USDOT-609tried", "carrier-005"),
    ("trk-035", "CA-SN-5004", "USDOT-609tried", "carrier-005"),
    ("trk-036", "CA-SN-5005", "USDOT-609tried", "carrier-005"),
    ("trk-037", "CA-SN-5006", "USDOT-609tried", "carrier-005"),
    # Landstar — 2 trucks on SF→LA route
    ("trk-038", "CA-LS-6001", "USDOT-1028580", "carrier-006"),
    ("trk-039", "CA-LS-6002", "USDOT-1028580", "carrier-006"),
    # UPS — 11 trucks (fallback)
    ("trk-040", "US-UP-7001", "USDOT-2328610", "carrier-007"),
    ("trk-041", "US-UP-7002", "USDOT-2328610", "carrier-007"),
    ("trk-042", "US-UP-7003", "USDOT-2328610", "carrier-007"),
    ("trk-043", "US-UP-7004", "USDOT-2328610", "carrier-007"),
    ("trk-044", "US-UP-7005", "USDOT-2328610", "carrier-007"),
    ("trk-045", "US-UP-7006", "USDOT-2328610", "carrier-007"),
    ("trk-046", "US-UP-7007", "USDOT-2328610", "carrier-007"),
    ("trk-047", "US-UP-7008", "USDOT-2328610", "carrier-007"),
    ("trk-048", "US-UP-7009", "USDOT-2328610", "carrier-007"),
    ("trk-049", "US-UP-7010", "USDOT-2328610", "carrier-007"),
    ("trk-050", "US-UP-7011", "USDOT-2328610", "carrier-007"),
    # FedEx — 9 trucks (fallback)
    ("trk-051", "US-FX-8001", "USDOT-680937", "carrier-008"),
    ("trk-052", "US-FX-8002", "USDOT-680937", "carrier-008"),
    ("trk-053", "US-FX-8003", "USDOT-680937", "carrier-008"),
    ("trk-054", "US-FX-8004", "USDOT-680937", "carrier-008"),
    ("trk-055", "US-FX-8005", "USDOT-680937", "carrier-008"),
    ("trk-056", "US-FX-8006", "USDOT-680937", "carrier-008"),
    ("trk-057", "US-FX-8007", "USDOT-680937", "carrier-008"),
    ("trk-058", "US-FX-8008", "USDOT-680937", "carrier-008"),
    ("trk-059", "US-FX-8009", "USDOT-680937", "carrier-008"),
]

# ---------------------------------------------------------------------------
# Helper to generate image + processing + sighting records for a truck trip
# ---------------------------------------------------------------------------

_img_counter = 0
_result_counter = 0
_sighting_counter = 0


def _make_pipeline_records(
    truck_id: str,
    license_plate: str,
    carrier_name: str,
    origin_cam: str,
    dest_cam: str,
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    trip_date: str,
    timestamp_depart: str,
    timestamp_arrive: str,
) -> tuple[list, list, list]:
    """Generate image_transactions, processing_results, and sightings for one truck journey."""
    global _img_counter, _result_counter, _sighting_counter

    images = []
    results = []
    sightings = []

    # Origin camera capture
    _img_counter += 1
    origin_img_id = f"img-{_img_counter:04d}"
    images.append((origin_img_id, origin_cam, timestamp_depart, f"s3://genlogs-images/{origin_img_id}.jpg", "clear", 55.0))

    _result_counter += 1
    results.append((f"res-{_result_counter:04d}", origin_img_id, "plate", license_plate, 0.95))
    _result_counter += 1
    results.append((f"res-{_result_counter:04d}", origin_img_id, "logo", carrier_name, 0.88))

    _sighting_counter += 1
    sightings.append((f"sight-{_sighting_counter:04d}", truck_id, origin_img_id, timestamp_depart, origin_lat, origin_lng, 0.94))

    # Destination camera capture
    _img_counter += 1
    dest_img_id = f"img-{_img_counter:04d}"
    images.append((dest_img_id, dest_cam, timestamp_arrive, f"s3://genlogs-images/{dest_img_id}.jpg", "clear", 60.0))

    _result_counter += 1
    results.append((f"res-{_result_counter:04d}", dest_img_id, "plate", license_plate, 0.97))
    _result_counter += 1
    results.append((f"res-{_result_counter:04d}", dest_img_id, "logo", carrier_name, 0.91))

    _sighting_counter += 1
    sightings.append((f"sight-{_sighting_counter:04d}", truck_id, dest_img_id, timestamp_arrive, dest_lat, dest_lng, 0.96))

    return images, results, sightings


# ---------------------------------------------------------------------------
# Build all trip + pipeline data
# ---------------------------------------------------------------------------

def _build_seed_data() -> dict:
    """Build the full seed dataset. Returns dict of entity lists."""
    all_images: list = []
    all_results: list = []
    all_sightings: list = []
    all_trips: list = []

    trip_counter = 0

    # Route configs: (truck_ids, carrier_id, origin, dest, cams, coords)
    route_configs = [
        # NY → DC: Knight-Swift (10), J.B. Hunt (7), YRC (5)
        {
            "trucks": [f"trk-{i:03d}" for i in range(1, 11)],
            "plates": [f"NY-KS-{1001 + i}" for i in range(10)],
            "carrier_id": "carrier-001",
            "carrier_name": "Knight-Swift Transport Services",
            "origin": "New York",
            "dest": "Washington DC",
            "origin_cam": "cam-001",
            "dest_cam": "cam-003",
            "origin_lat": 40.7580,
            "origin_lng": -73.9855,
            "dest_lat": 38.9072,
            "dest_lng": -77.0369,
        },
        {
            "trucks": [f"trk-{i:03d}" for i in range(11, 18)],
            "plates": [f"NY-JB-{2001 + i}" for i in range(7)],
            "carrier_id": "carrier-002",
            "carrier_name": "J.B. Hunt Transport Services Inc",
            "origin": "New York",
            "dest": "Washington DC",
            "origin_cam": "cam-002",
            "dest_cam": "cam-004",
            "origin_lat": 40.7214,
            "origin_lng": -74.0052,
            "dest_lat": 38.8816,
            "dest_lng": -77.0910,
        },
        {
            "trucks": [f"trk-{i:03d}" for i in range(18, 23)],
            "plates": [f"NY-YR-{3001 + i}" for i in range(5)],
            "carrier_id": "carrier-003",
            "carrier_name": "YRC Worldwide",
            "origin": "New York",
            "dest": "Washington DC",
            "origin_cam": "cam-001",
            "dest_cam": "cam-003",
            "origin_lat": 40.7580,
            "origin_lng": -73.9855,
            "dest_lat": 38.9072,
            "dest_lng": -77.0369,
        },
        # SF → LA: XPO (9), Schneider (6), Landstar (2)
        {
            "trucks": [f"trk-{i:03d}" for i in range(23, 32)],
            "plates": [f"CA-XP-{4001 + i}" for i in range(9)],
            "carrier_id": "carrier-004",
            "carrier_name": "XPO Logistics",
            "origin": "San Francisco",
            "dest": "Los Angeles",
            "origin_cam": "cam-005",
            "dest_cam": "cam-007",
            "origin_lat": 37.7749,
            "origin_lng": -122.4194,
            "dest_lat": 34.0522,
            "dest_lng": -118.2437,
        },
        {
            "trucks": [f"trk-{i:03d}" for i in range(32, 38)],
            "plates": [f"CA-SN-{5001 + i}" for i in range(6)],
            "carrier_id": "carrier-005",
            "carrier_name": "Schneider",
            "origin": "San Francisco",
            "dest": "Los Angeles",
            "origin_cam": "cam-006",
            "dest_cam": "cam-008",
            "origin_lat": 37.3382,
            "origin_lng": -121.8863,
            "dest_lat": 33.9425,
            "dest_lng": -118.4081,
        },
        {
            "trucks": [f"trk-{i:03d}" for i in range(38, 40)],
            "plates": [f"CA-LS-{6001 + i}" for i in range(2)],
            "carrier_id": "carrier-006",
            "carrier_name": "Landstar Systems",
            "origin": "San Francisco",
            "dest": "Los Angeles",
            "origin_cam": "cam-005",
            "dest_cam": "cam-007",
            "origin_lat": 37.7749,
            "origin_lng": -122.4194,
            "dest_lat": 34.0522,
            "dest_lng": -118.2437,
        },
        # Fallback routes: UPS (11) and FedEx (9) on Chicago → Detroit
        {
            "trucks": [f"trk-{i:03d}" for i in range(40, 51)],
            "plates": [f"US-UP-{7001 + i}" for i in range(11)],
            "carrier_id": "carrier-007",
            "carrier_name": "UPS Inc.",
            "origin": "Chicago",
            "dest": "Detroit",
            "origin_cam": "cam-001",
            "dest_cam": "cam-003",
            "origin_lat": 41.8781,
            "origin_lng": -87.6298,
            "dest_lat": 42.3314,
            "dest_lng": -83.0458,
        },
        {
            "trucks": [f"trk-{i:03d}" for i in range(51, 60)],
            "plates": [f"US-FX-{8001 + i}" for i in range(9)],
            "carrier_id": "carrier-008",
            "carrier_name": "FedEx Corp",
            "origin": "Chicago",
            "dest": "Detroit",
            "origin_cam": "cam-001",
            "dest_cam": "cam-003",
            "origin_lat": 41.8781,
            "origin_lng": -87.6298,
            "dest_lat": 42.3314,
            "dest_lng": -83.0458,
        },
    ]

    trip_date = "2026-03-15"

    for route in route_configs:
        for idx, truck_id in enumerate(route["trucks"]):
            hour_depart = 6 + (idx % 12)
            hour_arrive = hour_depart + 4

            imgs, res, sights = _make_pipeline_records(
                truck_id=truck_id,
                license_plate=route["plates"][idx],
                carrier_name=route["carrier_name"],
                origin_cam=route["origin_cam"],
                dest_cam=route["dest_cam"],
                origin_lat=route["origin_lat"],
                origin_lng=route["origin_lng"],
                dest_lat=route["dest_lat"],
                dest_lng=route["dest_lng"],
                trip_date=trip_date,
                timestamp_depart=f"{trip_date}T{hour_depart:02d}:00:00Z",
                timestamp_arrive=f"{trip_date}T{hour_arrive:02d}:30:00Z",
            )
            all_images.extend(imgs)
            all_results.extend(res)
            all_sightings.extend(sights)

            trip_counter += 1
            all_trips.append((
                f"trip-{trip_counter:04d}",
                truck_id,
                route["carrier_id"],
                route["origin"],
                route["dest"],
                trip_date,
            ))

    return {
        "images": all_images,
        "results": all_results,
        "sightings": all_sightings,
        "trips": all_trips,
    }


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------

def seed_database() -> None:
    """Create tables and seed data if not already present."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(Camera).count() > 0:
            return

        # Cameras
        for cam_id, lat, lng, highway in CAMERAS:
            db.add(Camera(camera_id=cam_id, latitude=lat, longitude=lng, highway_name=highway))

        # Carriers
        for cid, name, usdot, hq in CARRIERS:
            db.add(Carrier(carrier_id=cid, name=name, usdot_number=usdot, headquarters_city=hq))

        # Trucks
        for tid, plate, usdot, cid in TRUCKS:
            db.add(Truck(truck_id=tid, license_plate=plate, usdot_number=usdot, carrier_id=cid))

        # Pipeline data (images, processing results, sightings, trips)
        data = _build_seed_data()

        for img_id, cam_id, ts, path, weather, speed in data["images"]:
            db.add(ImageTransaction(
                image_id=img_id, camera_id=cam_id, timestamp=ts,
                storage_path=path, weather_conditions=weather, vehicle_speed=speed,
            ))

        for res_id, img_id, atype, val, conf in data["results"]:
            db.add(ImageProcessingResult(
                result_id=res_id, image_id=img_id, analysis_type=atype,
                detected_value=val, confidence_score=conf,
            ))

        for sid, tid, img_id, ts, lat, lng, conf in data["sightings"]:
            db.add(TruckSighting(
                sighting_id=sid, truck_id=tid, image_id=img_id,
                timestamp=ts, latitude=lat, longitude=lng, confidence_score=conf,
            ))

        for trip_id, tid, cid, origin, dest, tdate in data["trips"]:
            db.add(Trip(
                trip_id=trip_id, truck_id=tid, carrier_id=cid,
                origin_city=origin, destination_city=dest, trip_date=tdate,
            ))

        db.commit()
    finally:
        db.close()
