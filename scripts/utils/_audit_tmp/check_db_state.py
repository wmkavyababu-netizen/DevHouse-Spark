import sys, os, requests
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()
URL = os.environ['SUPABASE_URL'].rstrip('/')
KEY = os.environ.get('SUPABASE_SERVICE_KEY') or os.environ.get('SUPABASE_KEY')
H = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'}

# Check what dispatch event types exist
r = requests.get(URL + '/rest/v1/dispatches?select=event_type&limit=50', headers=H, timeout=10)
print('DISPATCH TYPES STATUS:', r.status_code)
if r.ok:
    types = set(d.get('event_type') for d in r.json())
    print(types)

# Check detections
r2 = requests.get(URL + '/rest/v1/detections?select=id,class_name,latitude,longitude,survey_id,review_status,detection_status&limit=20', headers=H, timeout=10)
print('DETECTIONS STATUS:', r2.status_code)
if r2.ok:
    for d in r2.json():
        print(' ', d['id'], '|', d['class_name'], '|', d.get('latitude'), d.get('longitude'), '| rev=', d.get('review_status'), '| det=', d.get('detection_status'))

# Check surveys table columns
r3 = requests.get(URL + '/rest/v1/surveys?select=*&limit=2', headers=H, timeout=10)
print('SURVEYS STATUS:', r3.status_code)
if r3.ok:
    rows = r3.json()
    if rows:
        print('SURVEY COLUMNS:', list(rows[0].keys()))
        print('FIRST SURVEY:', {k: v for k,v in rows[0].items() if k not in ('created_at',)})

# Check hotspots table (if it exists)
r4 = requests.get(URL + '/rest/v1/hotspots?select=*&limit=2', headers=H, timeout=10)
print('HOTSPOTS TABLE STATUS:', r4.status_code)
if r4.ok:
    print('HOTSPOTS:', r4.json())
else:
    print('HOTSPOTS ERROR:', r4.text[:200])
