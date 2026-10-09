#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seed_demo_survey.py — TARANG-DEMO-001 Canonical Demo Seeder
============================================================
Creates ONE deterministic demo survey in Supabase that all portals share.

Survey: Indian Ocean Marine Debris Demonstration Survey
ID:     TARANG-DEMO-001
Coords: 10.0000 N, 80.0000 E (Indian Ocean east of Sri Lanka)

Run once:  python seed_demo_survey.py
"""

import os, uuid, hashlib, datetime, requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    exit(1)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

# Deterministic UUID v5 so every re-run produces the exact same survey ID.
# surveys.survey_id is UUID type in Supabase.
DEMO_SURVEY_ID   = str(uuid.uuid5(uuid.NAMESPACE_DNS, "TARANG-DEMO-001"))  # 6d17c69e-...
DEMO_SURVEY_LABEL = "TARANG-DEMO-001"   # Human-readable display label
DEMO_SURVEY_NAME = "Indian Ocean Marine Debris Demonstration Survey"
NOW = datetime.datetime.now(datetime.timezone.utc)


# Demo track points lawnmower around 10.0N 80.0E
DEMO_TRACK = [
    (10.0000, 80.0000),
    (10.0100, 80.0150),
    (10.0200, 80.0050),
    (10.0150, 79.9850),
    (9.9950,  79.9900),
]

def stable_id(seq):
    return "DET-" + hashlib.sha256(f"TARANG-DEMO-001:{seq}".encode()).hexdigest()[:12].upper()

DEMO_DETECTIONS = [
    {
        "id":                   stable_id("0"),
        "survey_id":            DEMO_SURVEY_ID,
        "class_name":           "ghost_net",
        "title":                "Ghost Drift Net (Entangled)",
        "category":             "Bio-Hazard Entanglement",
        "confidence":           91.4,
        "classification_tier":  "A",
        "requires_review":      False,
        "latitude":             10.0100,
        "longitude":            80.0150,
        "ping_number":          312,
        "depth":                "-42.3m",
        "altitude":             "3.1m",
        "heading":              95.2,
        "material":             "Monofilament Nylon-6",
        "hazard":               "High Marine Entanglement Risk",
        "crop_url":             "",
        "created_at":           NOW.isoformat(),
    },
    {
        "id":                   stable_id("1"),
        "survey_id":            DEMO_SURVEY_ID,
        "class_name":           "shipwreck",
        "title":                "Historic Shipwreck / Vessel Structure",
        "category":             "Submerged Archaeological Feature",
        "confidence":           87.6,
        "classification_tier":  "A",
        "requires_review":      False,
        "latitude":             10.0200,
        "longitude":            80.0050,
        "ping_number":          521,
        "depth":                "-51.0m",
        "altitude":             "2.8m",
        "heading":              110.4,
        "material":             "Reinforced Timber & Steel Clad",
        "hazard":               "Navigation Clearance Hazard",
        "crop_url":             "",
        "created_at":           NOW.isoformat(),
    },
    {
        "id":                   stable_id("2"),
        "survey_id":            DEMO_SURVEY_ID,
        "class_name":           "crab_pot",
        "title":                "Derelict Crab / Fish Trap",
        "category":             "Derelict Fishing Gear",
        "confidence":           78.2,
        "classification_tier":  "B",
        "requires_review":      True,
        "latitude":             10.0150,
        "longitude":            79.9850,
        "ping_number":          187,
        "depth":                "-38.7m",
        "altitude":             "4.5m",
        "heading":              275.0,
        "material":             "Galvanized Steel Wire Mesh",
        "hazard":               "Benthic Habitat Smothering",
        "crop_url":             "",
        "created_at":           NOW.isoformat(),
    },
    {
        "id":                   stable_id("3"),
        "survey_id":            DEMO_SURVEY_ID,
        "class_name":           "mine_cylinder",
        "title":                "Cylindrical Anomaly / Ordnance Risk",
        "category":             "High Threat Subsea Munition",
        "confidence":           84.6,
        "classification_tier":  "A",
        "requires_review":      False,
        "latitude":             9.9950,
        "longitude":            79.9900,
        "ping_number":          95,
        "depth":                "-29.5m",
        "altitude":             "5.2m",
        "heading":              200.1,
        "material":             "Heavy Ferrous Metal Casing",
        "hazard":               "Pending Classification",
        "crop_url":             "",
        "created_at":           NOW.isoformat(),
    },
    {
        "id":                   stable_id("4"),
        "survey_id":            DEMO_SURVEY_ID,
        "class_name":           "submarine_pipeline",
        "title":                "Submarine Pipeline / Power Conduit",
        "category":             "Underwater Critical Infrastructure",
        "confidence":           76.3,
        "classification_tier":  "B",
        "requires_review":      True,
        "latitude":             10.0050,
        "longitude":            80.0080,
        "ping_number":          430,
        "depth":                "-45.1m",
        "altitude":             "3.7m",
        "heading":              45.5,
        "material":             "Coated Subsea Alloy",
        "hazard":               "Structural Integrity Survey",
        "crop_url":             "",
        "created_at":           NOW.isoformat(),
    },
]

DEMO_SURVEY = {
    "survey_id":          DEMO_SURVEY_ID,
    "survey_name":        DEMO_SURVEY_NAME,
    "survey_date":        "2026-09-21",
    "survey_time":        "09:00",
    "location_name":      "Indian Ocean / Bay of Bengal — Demonstration Region (10N 80E)",
    "sonar_device":       "EdgeTech 4200 Side-Scan Sonar (TARANG Demo)",
    "sonar_frequency":    "400/900 kHz",
    "created_by":         "DEMO-SURVEY",
    "created_at":         "2026-09-21T09:00:00",
    "status":             "active",
    "navigation_status":  "COMPLETED",
    "processing_status":  "completed",
}

def exists_survey():
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/surveys?survey_id=eq.{DEMO_SURVEY_ID}&select=survey_id",
        headers=HEADERS, timeout=10
    )
    return r.status_code == 200 and bool(r.json())

def exists_detection(det_id):
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/detections?id=eq.{det_id}&select=id",
        headers=HEADERS, timeout=10
    )
    return r.status_code == 200 and bool(r.json())

print("=" * 60)
print("TARANG DEMO SURVEY SEEDER")
print("=" * 60)

if exists_survey():
    print(f"[OK]  Survey already exists: {DEMO_SURVEY_ID}")
else:
    h = {**HEADERS, "Prefer": "return=minimal"}
    r = requests.post(f"{SUPABASE_URL}/rest/v1/surveys", json=DEMO_SURVEY, headers=h, timeout=15)
    if r.status_code in (200, 201):
        print(f"[OK]  Survey created: {DEMO_SURVEY_ID}")
    else:
        print(f"[ERR] Survey creation failed: {r.status_code} {r.text[:400]}")

for det in DEMO_DETECTIONS:
    if exists_detection(det["id"]):
        print(f"[OK]  Detection already exists: {det['id']} ({det['class_name']})")
    else:
        h = {**HEADERS, "Prefer": "return=minimal"}
        r = requests.post(f"{SUPABASE_URL}/rest/v1/detections", json=det, headers=h, timeout=15)
        if r.status_code in (200, 201):
            print(f"[OK]  Detection created: {det['id']} ({det['class_name']}) @ {det['latitude']},{det['longitude']}")
        else:
            print(f"[ERR] Detection creation failed: {r.status_code} {r.text[:400]}")

try:
    ev = {
        "survey_id": DEMO_SURVEY_ID,
        "file_name": "tarang_indian_ocean_demo.xtf",
        "file_type": "XTF",
        "file_hash": hashlib.sha256(b"TARANG-DEMO-001").hexdigest(),
        "uploaded_at": "2026-09-21T09:00:00",
        "processing_status": "completed",
        "source_label": "TARANG Indian Ocean Demonstration Survey (XTF)",
        "metadata": {
            "Survey ID": DEMO_SURVEY_ID,
            "Survey Name": DEMO_SURVEY_NAME,
            "SonarName": "EdgeTech 4200 Side-Scan Sonar",
            "Total Pings": 5000,
            "Channel Count": 2,
            "Min Latitude":  9.9950,
            "Max Latitude": 10.0200,
            "Min Longitude": 79.9850,
            "Max Longitude": 80.0150,
            "Start Time": "2026-09-21T09:00:00",
            "End Time":   "2026-09-21T10:23:00",
            "Avg Depth": "41.3m",
            "Note": "DEMONSTRATION DATA - Indian Ocean Offshore Region",
        }
    }
    h = {**HEADERS, "Prefer": "return=minimal"}
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/dispatches",
        json={"event_type": "survey_uploaded", "payload": ev, "created_at": NOW.isoformat()},
        headers=h, timeout=15
    )
    if r.status_code in (200, 201):
        print("[OK]  Dispatch survey_uploaded event logged")
    else:
        print(f"[WARN] Dispatch event: {r.status_code} {r.text[:200]}")
except Exception as e:
    print(f"[WARN] Dispatch event error: {e}")

print()
print("Done. TARANG-DEMO-001 is ready for all portals.")
