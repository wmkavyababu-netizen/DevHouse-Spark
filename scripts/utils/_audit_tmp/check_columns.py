import sys, os, requests, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()
URL = os.environ['SUPABASE_URL'].rstrip('/')
KEY = os.environ.get('SUPABASE_SERVICE_KEY') or os.environ.get('SUPABASE_KEY')
H = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'}

# Check detections columns  
r = requests.get(URL + '/rest/v1/detections?select=*&limit=2', headers=H, timeout=10)
print('DETECTIONS STATUS:', r.status_code)
if r.ok:
    rows = r.json()
    if rows:
        print('DETECTION COLUMNS:', list(rows[0].keys()))
        for row in rows:
            print(json.dumps({k:v for k,v in row.items() if k not in ('crop_url','created_at')}, indent=2))
    else:
        print('No detections found')
else:
    print('ERROR:', r.text[:500])

# Check dispatches for cleanup_operation specifically
r2 = requests.get(URL + '/rest/v1/dispatches?event_type=eq.cleanup_operation&limit=10', headers=H, timeout=10)
print('CLEANUP_OPERATION DISPATCHES:', r2.status_code)
print(r2.json())

# Check dispatches for verification
r3 = requests.get(URL + '/rest/v1/dispatches?event_type=eq.detection_verification&limit=5', headers=H, timeout=10)
print('VERIFICATION DISPATCHES:', r3.status_code)
if r3.ok:
    for d in r3.json():
        print(json.dumps(d, indent=2, default=str))
        
# Check hotspots table columns
r4 = requests.get(URL + '/rest/v1/hotspots?select=*&limit=1', headers=H, timeout=10)
print('HOTSPOTS COLUMNS STATUS:', r4.status_code)
if r4.ok and r4.json():
    print('HOTSPOT COLS:', list(r4.json()[0].keys()))
else:
    # Try to get column info another way
    print('HOTSPOTS EMPTY OR ERROR:', r4.text[:200])
