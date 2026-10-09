"""
seed_hotspot_route.py — Seed hotspot_cleanup_route dispatch event
=================================================================
The government portal reads hotspot_cleanup_route events (not route_optimized).
This seeder computes 2 DBSCAN hotspot clusters from demo detections and persists
a hotspot_cleanup_route dispatch event so the gov portal shows a live route.
Run after seed_demo_full.py.
"""
import os, sys, uuid, hashlib, math, datetime, json, requests
from dotenv import load_dotenv
load_dotenv()

URL = os.environ['SUPABASE_URL'].rstrip('/')
KEY = os.environ.get('SUPABASE_SERVICE_KEY') or os.environ.get('SUPABASE_KEY')
H = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json', 'Prefer': 'return=minimal'}
HR = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json', 'Prefer': 'return=representation'}

DEMO_SURVEY_ID = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'TARANG-DEMO-001'))
NOW = datetime.datetime.now(datetime.timezone.utc)

def haversine_nm(p1, p2):
    R_NM = 3440.065
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlat, dlon = lat2-lat1, lon2-lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return R_NM * 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0,1-a)))

def haversine_km(p1, p2):
    return haversine_nm(p1, p2) * 1.852

# Two DBSCAN-derived clusters from the demo detections (eps=2000m):
# Cluster 1: DET1(10.01,80.015), DET2(10.02,80.005), DET5(10.005,80.008) → center ~10.012, 80.009
# Cluster 2: DET3(10.015,79.985), DET4(9.995,79.99) → center ~10.005, 79.988

HOTSPOTS = [
    {
        'id': 'HS-' + hashlib.sha256('DET-FFF7EAD064AC|DET-8A97730739EC|DET-C929983001CF'.encode()).hexdigest()[:10].upper(),
        'label': 'Acoustic Hazard Cluster 01',
        'latitude': round((10.01 + 10.02 + 10.005) / 3, 6),
        'longitude': round((80.015 + 80.005 + 80.008) / 3, 6),
        'detection_count': 3,
        'priority': 'High',
        'dominant_type': 'Ghost Net',
        'target_classes': ['ghost_net', 'shipwreck', 'submarine_pipeline'],
        'status': 'Cleanup Approved',
        'survey_id': DEMO_SURVEY_ID,
    },
    {
        'id': 'HS-' + hashlib.sha256('DET-858480EDB4CE|DET-391457CB668C'.encode()).hexdigest()[:10].upper(),
        'label': 'Acoustic Hazard Cluster 02',
        'latitude': round((10.015 + 9.995) / 2, 6),
        'longitude': round((79.985 + 79.990) / 2, 6),
        'detection_count': 2,
        'priority': 'High',
        'dominant_type': 'Mine Cylinder',
        'target_classes': ['crab_pot', 'mine_cylinder'],
        'status': 'Cleanup Approved',
        'survey_id': DEMO_SURVEY_ID,
    },
]

# Check if hotspot_cleanup_route already exists
r = requests.get(URL + '/rest/v1/dispatches?event_type=eq.hotspot_cleanup_route&limit=5', headers=HR, timeout=10)
existing = r.json() if r.ok else []
if existing:
    print('[OK]  hotspot_cleanup_route already exists (' + str(len(existing)) + ' events)')
    sys.exit(0)

# Build nearest-neighbour route from depot
DEPOT = [10.0000, 80.0000]
start = {'latitude': DEPOT[0], 'longitude': DEPOT[1], 'label': 'Start Point (Depot)', 'is_start': True}

# Build leg sequence
hs_copy = list(HOTSPOTS)
ordered = []
curr = DEPOT
while hs_copy:
    nxt = min(hs_copy, key=lambda h: haversine_nm(curr, [h['latitude'], h['longitude']]))
    hs_copy.remove(nxt)
    ordered.append(nxt)
    curr = [nxt['latitude'], nxt['longitude']]

total_nm = haversine_nm(DEPOT, [ordered[0]['latitude'], ordered[0]['longitude']])
legs = []
prev = DEPOT
prev_label = 'Start Point'
for idx, hs in enumerate(ordered, 1):
    d_nm = haversine_nm(prev, [hs['latitude'], hs['longitude']])
    d_km = haversine_km(prev, [hs['latitude'], hs['longitude']])
    legs.append({
        'from': prev_label,
        'to': hs['label'],
        'distance_nm': round(d_nm, 3),
        'distance_km': round(d_km, 3),
    })
    total_nm += d_nm if idx > 1 else 0
    prev = [hs['latitude'], hs['longitude']]
    prev_label = hs['label']

# Return leg
return_nm = haversine_nm(prev, DEPOT)
legs.append({'from': prev_label, 'to': 'Start Point', 'distance_nm': round(return_nm, 3), 'distance_km': round(return_nm * 1.852, 3)})

# Recalculate total properly
total_nm = sum(leg['distance_nm'] for leg in legs)
total_km = sum(leg['distance_km'] for leg in legs)
ordered_ids = [hs['id'] for hs in ordered]
route_id = 'ROUTE-HS-' + hashlib.sha256('|'.join(ordered_ids).encode()).hexdigest()[:12].upper()

waypoints = [{'hotspot_id': hs['id'], 'label': hs['label'], 'latitude': hs['latitude'], 'longitude': hs['longitude'],
               'sequence': i+1, 'priority': hs['priority'], 'detection_count': hs['detection_count'],
               'target_classes': hs['target_classes']} for i, hs in enumerate(ordered)]

route_payload = {
    'route_id': route_id,
    'survey_id': DEMO_SURVEY_ID,
    'algorithm': 'nearest-neighbour (heuristic)',
    'unit': 'NM',
    'start_point': {'latitude': DEPOT[0], 'longitude': DEPOT[1], 'label': 'Start Point'},
    'hotspot_count': len(ordered),
    'ordered_hotspots': ordered_ids,
    'target_sequence': waypoints,
    'legs': legs,
    'total_distance_nm': round(total_nm, 3),
    'total_distance_km': round(total_km, 3),
    'total_distance_m': round(total_km * 1000, 1),
    'distance_display': str(round(total_nm, 2)) + ' NM (' + str(round(total_km, 1)) + ' km)',
    'route_coordinates': [[DEPOT[0], DEPOT[1]]] + [[hs['latitude'], hs['longitude']] for hs in ordered] + [[DEPOT[0], DEPOT[1]]],
    'estimated_travel_minutes': round(total_nm / 12 * 60),
    'planning_speed_knots': 12,
    'generated_at': '2026-09-21T10:00:00+00:00',
}

row = {'event_type': 'hotspot_cleanup_route', 'payload': route_payload, 'created_at': NOW.isoformat()}
r2 = requests.post(URL + '/rest/v1/dispatches', json=row, headers=H, timeout=12)
if r2.status_code in (200, 201):
    print('[OK]  hotspot_cleanup_route seeded: ' + route_id)
    print('      Route: ' + str(len(ordered)) + ' hotspots | ' + str(round(total_nm, 2)) + ' NM (' + str(round(total_km, 1)) + ' km)')
    for leg in legs:
        print('      ' + leg['from'] + ' → ' + leg['to'] + ' : ' + str(leg['distance_nm']) + ' NM')
else:
    print('[ERR] Failed: ' + r2.text[:200])
