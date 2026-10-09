#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seed_demo_full.py — TARANG-DEMO-001 Complete End-to-End Data Seeder
=====================================================================
Creates ALL demo records in Supabase so every portal works out of the box:
  - Survey + 5 Detections  (already done by seed_demo_survey.py)
  - detection_state events  → makes detections show as "Verified"
  - detection_verification  → analyst verification record
  - cleanup_operation events → allows TSP route generation
  - route_optimized event   → so marine/gov portals show a persisted route

Run once:  python seed_demo_full.py
Idempotent: safe to re-run — checks before inserting.
"""

import os, sys, uuid, hashlib, datetime, json, math, requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    sys.exit(1)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": "Bearer " + SUPABASE_KEY,
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}
HEADERS_REPR = {
    "apikey": SUPABASE_KEY,
    "Authorization": "Bearer " + SUPABASE_KEY,
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

# ── Canonical IDs ────────────────────────────────────────────────────────────
DEMO_SURVEY_ID = str(uuid.uuid5(uuid.NAMESPACE_DNS, "TARANG-DEMO-001"))
DEMO_SURVEY_NAME = "Indian Ocean Marine Debris Demonstration Survey"
NOW = datetime.datetime.now(datetime.timezone.utc)
SEED_TS = "2026-09-21T09:00:00+00:00"


def stable_det_id(seq):
    return "DET-" + hashlib.sha256(("TARANG-DEMO-001:" + str(seq)).encode()).hexdigest()[:12].upper()


DEMO_DETS = [
    {
        "id": stable_det_id("0"),
        "class_name": "ghost_net",
        "title": "Ghost Drift Net (Entangled)",
        "category": "Bio-Hazard Entanglement",
        "confidence": 91.4,
        "classification_tier": "A",
        "requires_review": False,
        "latitude": 10.0100,
        "longitude": 80.0150,
        "ping_number": 312,
        "depth": "-42.3m",
        "altitude": "3.1m",
        "heading": 95.2,
        "material": "Monofilament Nylon-6",
        "hazard": "High Marine Entanglement Risk",
    },
    {
        "id": stable_det_id("1"),
        "class_name": "shipwreck",
        "title": "Historic Shipwreck / Vessel Structure",
        "category": "Submerged Archaeological Feature",
        "confidence": 87.6,
        "classification_tier": "A",
        "requires_review": False,
        "latitude": 10.0200,
        "longitude": 80.0050,
        "ping_number": 521,
        "depth": "-51.0m",
        "altitude": "2.8m",
        "heading": 110.4,
        "material": "Reinforced Timber & Steel Clad",
        "hazard": "Navigation Clearance Hazard",
    },
    {
        "id": stable_det_id("2"),
        "class_name": "crab_pot",
        "title": "Derelict Crab / Fish Trap",
        "category": "Derelict Fishing Gear",
        "confidence": 78.2,
        "classification_tier": "B",
        "requires_review": False,  # fixed: mark as verified
        "latitude": 10.0150,
        "longitude": 79.9850,
        "ping_number": 187,
        "depth": "-38.7m",
        "altitude": "4.5m",
        "heading": 275.0,
        "material": "Galvanized Steel Wire Mesh",
        "hazard": "Benthic Habitat Smothering",
    },
    {
        "id": stable_det_id("3"),
        "class_name": "mine_cylinder",
        "title": "Cylindrical Anomaly / Ordnance Risk",
        "category": "High Threat Subsea Munition",
        "confidence": 84.6,
        "classification_tier": "A",
        "requires_review": False,
        "latitude": 9.9950,
        "longitude": 79.9900,
        "ping_number": 95,
        "depth": "-29.5m",
        "altitude": "5.2m",
        "heading": 200.1,
        "material": "Heavy Ferrous Metal Casing",
        "hazard": "Pending Classification",
    },
    {
        "id": stable_det_id("4"),
        "class_name": "submarine_pipeline",
        "title": "Submarine Pipeline / Power Conduit",
        "category": "Underwater Critical Infrastructure",
        "confidence": 76.3,
        "classification_tier": "B",
        "requires_review": False,  # fixed: mark as verified
        "latitude": 10.0050,
        "longitude": 80.0080,
        "ping_number": 430,
        "depth": "-45.1m",
        "altitude": "3.7m",
        "heading": 45.5,
        "material": "Coated Subsea Alloy",
        "hazard": "Structural Integrity Survey",
    },
]

# TSP start depot
DEPOT_LAT, DEPOT_LON = 10.0000, 80.0000


# ── Helper functions ──────────────────────────────────────────────────────────

def sb_get(table, query=""):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}?{query}", headers=HEADERS_REPR, timeout=12)
    return r.status_code, r.json() if r.ok else []


def sb_post(table, payload):
    r = requests.post(f"{SUPABASE_URL}/rest/v1/{table}", json=payload, headers=HEADERS, timeout=12)
    return r.status_code in (200, 201), r.text[:200]


def sb_patch(table, query, payload):
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/{table}?{query}", json=payload, headers=HEADERS, timeout=12)
    return r.status_code in (200, 204), r.text[:200]


def log_dispatch(event_type, payload):
    row = {"event_type": event_type, "payload": payload, "created_at": NOW.isoformat()}
    return sb_post("dispatches", row)


def dispatch_exists(event_type, key, value):
    status, rows = sb_get("dispatches", f"event_type=eq.{event_type}&limit=100")
    if status != 200:
        return False
    for row in rows:
        p = row.get("payload") or {}
        if str(p.get(key, "")) == str(value):
            return True
    return False


def haversine_km(p1, p2):
    R = 6371.0
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1 - a)))


# ── 1. Ensure survey exists ───────────────────────────────────────────────────
print("=" * 60)
print("TARANG FULL DEMO SEEDER")
print("=" * 60)

status, surveys = sb_get("surveys", f"survey_id=eq.{DEMO_SURVEY_ID}&select=survey_id")
if status == 200 and surveys:
    print(f"[OK]  Survey {DEMO_SURVEY_ID} already exists")
else:
    ok, msg = sb_post("surveys", {
        "survey_id": DEMO_SURVEY_ID,
        "survey_name": DEMO_SURVEY_NAME,
        "survey_date": "2026-09-21",
        "survey_time": "09:00",
        "location_name": "Indian Ocean / Bay of Bengal — Demonstration Region (10N 80E)",
        "sonar_device": "EdgeTech 4200 Side-Scan Sonar (TARANG Demo)",
        "sonar_frequency": "400/900 kHz",
        "created_by": "DEMO-SURVEY",
        "status": "active",
        "navigation_status": "COMPLETED",
        "processing_status": "completed",
    })
    print(f"{'[OK] ' if ok else '[ERR]'} Survey created: {msg[:80]}")

# ── 2. Ensure detections exist + update requires_review ─────────────────────
for det in DEMO_DETS:
    _, existing = sb_get("detections", f"id=eq.{det['id']}&select=id,requires_review")
    if existing:
        # Patch requires_review=false so _state_from_detection returns "Verified"
        ok, msg = sb_patch("detections", f"id=eq.{det['id']}", {"requires_review": False})
        print(f"[OK]  Detection {det['id']} exists — patched requires_review=false")
    else:
        row = dict(det)
        row["survey_id"] = DEMO_SURVEY_ID
        row["created_at"] = SEED_TS
        row["crop_url"] = ""
        ok, msg = sb_post("detections", row)
        print(f"{'[OK] ' if ok else '[ERR]'} Detection {det['id']} created: {msg[:60]}")

# ── 3. detection_state events → Verified status ──────────────────────────────
print("\n--- Verification state events ---")
for det in DEMO_DETS:
    if dispatch_exists("detection_state", "detection_id", det["id"]):
        print(f"[OK]  detection_state already exists for {det['id']}")
        continue
    payload = {
        "detection_id": det["id"],
        "survey_id": DEMO_SURVEY_ID,
        "status": "verified",
        "reviewer": "demo-sonar",
        "ai_class": det["class_name"],
        "ai_confidence": det["confidence"],
        "analyst_class": det["class_name"],
        "analyst_status": "Verified",
        "verified_at": SEED_TS,
        "event_type": "detection_state",
        "notes": "DEMONSTRATION DATA — automatically verified for TARANG-DEMO-001",
    }
    ok, msg = log_dispatch("detection_state", payload)
    print(f"{'[OK] ' if ok else '[ERR]'} detection_state for {det['id']}: {msg[:60]}")

# ── 4. detection_verification events ─────────────────────────────────────────
print("\n--- Analyst verification events ---")
for det in DEMO_DETS:
    if dispatch_exists("detection_verification", "detection_id", det["id"]):
        print(f"[OK]  detection_verification already exists for {det['id']}")
        continue
    payload = {
        "detection_id": det["id"],
        "survey_id": DEMO_SURVEY_ID,
        "ai_class": det["class_name"],
        "ai_confidence": det["confidence"],
        "analyst_class": det["class_name"],
        "analyst_status": "Verified",
        "reviewer": "demo-sonar",
        "verified_at": SEED_TS,
        "notes": "DEMONSTRATION DATA",
        "event_type": "detection_verification",
    }
    ok, msg = log_dispatch("detection_verification", payload)
    print(f"{'[OK] ' if ok else '[ERR]'} detection_verification for {det['id']}: {msg[:60]}")

# ── 5. cleanup_operation dispatch events (needed for TSP) ────────────────────
print("\n--- Cleanup operation dispatch events ---")
for i, det in enumerate(DEMO_DETS):
    op_id = f"OPS-DEMO-{i+1:03d}"
    if dispatch_exists("cleanup_operation", "target_id", det["id"]):
        print(f"[OK]  cleanup_operation already exists for {det['id']}")
        continue
    payload = {
        "operation_id": op_id,
        "target_id": det["id"],
        "survey_id": DEMO_SURVEY_ID,
        "hotspot_id": None,
        "target_type": det["title"],
        "latitude": det["latitude"],
        "longitude": det["longitude"],
        "priority": "High" if det["confidence"] >= 80 else "Medium",
        "status": "Cleanup Approved",
        "progress_percent": 0,
        "assigned_operation": "Marine Response Fleet A (TARANG Demo)",
        "notes": "DEMONSTRATION DATA — Indian Ocean offshore sector",
        "approved_at": SEED_TS,
    }
    ok, msg = log_dispatch("cleanup_operation", payload)
    print(f"{'[OK] ' if ok else '[ERR]'} cleanup_operation {op_id} for {det['id']}: {msg[:60]}")

# ── 6. TSP route_optimized dispatch event ────────────────────────────────────
print("\n--- TSP route_optimized dispatch event ---")
ROUTE_ID = "ROUTE-" + hashlib.sha256("TARANG-DEMO-001-ROUTE".encode()).hexdigest()[:12].upper()

if dispatch_exists("route_optimized", "route_id", ROUTE_ID):
    print(f"[OK]  route_optimized already exists: {ROUTE_ID}")
else:
    # Nearest-neighbour TSP from depot
    targets = [{"id": d["id"], "lat": d["latitude"], "lon": d["longitude"], "title": d["title"], "confidence": d["confidence"]} for d in DEMO_DETS]
    remaining = list(targets)
    seq = []
    curr = [DEPOT_LAT, DEPOT_LON]
    while remaining:
        nxt = min(remaining, key=lambda t: haversine_km(curr, [t["lat"], t["lon"]]))
        remaining.remove(nxt)
        seq.append(nxt)
        curr = [nxt["lat"], nxt["lon"]]

    total_dist = haversine_km([DEPOT_LAT, DEPOT_LON], [seq[0]["lat"], seq[0]["lon"]])
    for k in range(1, len(seq)):
        total_dist += haversine_km([seq[k-1]["lat"], seq[k-1]["lon"]], [seq[k]["lat"], seq[k]["lon"]])
    total_dist += haversine_km([seq[-1]["lat"], seq[-1]["lon"]], [DEPOT_LAT, DEPOT_LON])

    target_sequence = []
    leg_dist_acc = 0.0
    prev = [DEPOT_LAT, DEPOT_LON]
    for idx, t in enumerate(seq, 1):
        leg = haversine_km(prev, [t["lat"], t["lon"]])
        leg_dist_acc += leg
        target_sequence.append({
            "sequence": idx,
            "target_id": t["id"],
            "operation_id": f"OPS-DEMO-{DEMO_DETS.index(next(d for d in DEMO_DETS if d['id']==t['id']))+1:03d}",
            "survey_id": DEMO_SURVEY_ID,
            "latitude": t["lat"],
            "longitude": t["lon"],
            "target_type": t["title"],
            "priority": "High" if t["confidence"] >= 80 else "Medium",
            "status": "Cleanup Approved",
            "leg_distance_km": round(leg, 3),
            "coordinates": [t["lat"], t["lon"]],
        })
        prev = [t["lat"], t["lon"]]

    route_payload = {
        "route_id": ROUTE_ID,
        "survey_id": DEMO_SURVEY_ID,
        "status": "Route Generated",
        "target_count": len(seq),
        "distance_km": round(total_dist, 3),
        "route_coordinates": [[t["lat"], t["lon"]] for t in seq],
        "target_sequence": target_sequence,
        "estimated_travel_minutes": round(total_dist / 18.0 * 60),
        "estimated_cleanup_minutes": len(seq) * 35,
        "estimated_operation_hours": round((round(total_dist / 18.0 * 60) + len(seq) * 35) / 60, 1),
        "route_status": "Ready for scheduling",
        "generated_at": SEED_TS,
    }
    ok, msg = log_dispatch("route_optimized", route_payload)
    print(f"{'[OK] ' if ok else '[ERR]'} route_optimized {ROUTE_ID}: {msg[:60]}")
    print(f"       Route: {len(seq)} targets | {round(total_dist,3)} km total")
    for s in target_sequence:
        print(f"       {s['sequence']}. {s['target_id']} @ {s['latitude']},{s['longitude']} — {s['leg_distance_km']} km")

# ── 7. survey_created dispatch event ─────────────────────────────────────────
print("\n--- Survey created dispatch event ---")
if not dispatch_exists("survey_created", "survey_id", DEMO_SURVEY_ID):
    ok, msg = log_dispatch("survey_created", {
        "survey_id": DEMO_SURVEY_ID,
        "survey_name": DEMO_SURVEY_NAME,
        "created_by": "DEMO-SURVEY",
        "created_at": SEED_TS,
    })
    print(f"{'[OK] ' if ok else '[ERR]'} survey_created dispatch: {msg[:60]}")
else:
    print(f"[OK]  survey_created dispatch already exists")

print()
print("=" * 60)
print("TARANG-DEMO-001 full seed complete.")
print(f"Survey ID : {DEMO_SURVEY_ID}")
print(f"Detections: {len(DEMO_DETS)}")
print(f"Route ID  : {ROUTE_ID}")
print("=" * 60)
