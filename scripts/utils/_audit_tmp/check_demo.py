import sys, os, requests, json, uuid
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()
URL = os.environ['SUPABASE_URL'].rstrip('/')
KEY = os.environ.get('SUPABASE_SERVICE_KEY') or os.environ.get('SUPABASE_KEY')
H = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'}

DEMO_UUID = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'TARANG-DEMO-001'))
print('DEMO_UUID:', DEMO_UUID)

# Check if demo survey exists
r = requests.get(URL + '/rest/v1/surveys?survey_id=eq.' + DEMO_UUID + '&select=*', headers=H, timeout=10)
print('DEMO SURVEY:', r.status_code, r.json())

# Check demo detections with correct columns
r2 = requests.get(URL + '/rest/v1/detections?survey_id=eq.' + DEMO_UUID + '&select=id,class_name,latitude,longitude,verification_status,clearance_status', headers=H, timeout=10)
print('DEMO DETECTIONS STATUS:', r2.status_code)
if r2.ok:
    dets = r2.json()
    print(f'Found {len(dets)} demo detections:')
    for d in dets:
        print(' ', d['id'], d['class_name'], d['latitude'], d['longitude'], 'verif=', d.get('verification_status'))
else:
    print('ERROR:', r2.text[:300])

# Check supabase_service get_all_detections query
lines = open('supabase_service.py', encoding='utf-8', errors='replace').readlines()
for i, l in enumerate(lines):
    if 'def get_all_detections' in l:
        print('\nget_all_detections function starts at line', i+1)
        for j in range(i, min(i+30, len(lines))):
            print(f'{j+1}: {lines[j].rstrip()}')
        break
