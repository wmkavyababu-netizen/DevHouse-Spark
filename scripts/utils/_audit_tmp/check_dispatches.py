import sys, os, requests
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()
URL = os.environ['SUPABASE_URL'].rstrip('/')
KEY = os.environ.get('SUPABASE_SERVICE_KEY') or os.environ.get('SUPABASE_KEY')
H = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY}

# Check hotspot_cleanup_route
r = requests.get(URL + '/rest/v1/dispatches?event_type=eq.hotspot_cleanup_route&order=created_at.desc&limit=3', headers=H)
print('hotspot_cleanup_route status:', r.status_code)
rows = r.json() if r.ok else []
print('Count:', len(rows))
for row in rows:
    p = row.get('payload') or {}
    print(' Route:', p.get('route_id'), '| hotspots:', p.get('hotspot_count'), '| created:', row.get('created_at', 'N/A')[:25])

# Check route_optimized
r2 = requests.get(URL + '/rest/v1/dispatches?event_type=eq.route_optimized&order=created_at.desc&limit=3', headers=H)
print('\nroute_optimized status:', r2.status_code, '| count:', len(r2.json() if r2.ok else []))

# Check cleanup_operation
r3 = requests.get(URL + '/rest/v1/dispatches?event_type=eq.cleanup_operation&order=created_at.desc&limit=5', headers=H)
print('cleanup_operation status:', r3.status_code)
if r3.ok:
    for row in r3.json():
        p = row.get('payload') or {}
        print(' Op:', p.get('operation_id'), '| target:', p.get('target_id'), '| status:', p.get('status'), '| lat:', p.get('latitude'))

# Check detection_state
r4 = requests.get(URL + '/rest/v1/dispatches?event_type=eq.detection_state&order=created_at.desc&limit=5', headers=H)
print('\ndetection_state events:', r4.status_code, '| count:', len(r4.json() if r4.ok else []))
if r4.ok:
    for row in r4.json()[:2]:
        p = row.get('payload') or {}
        print(' Det:', p.get('detection_id'), '| status:', p.get('status'), '| lifecycle:', p.get('lifecycle_status'))
