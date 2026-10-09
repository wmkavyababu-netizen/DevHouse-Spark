import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'c:\Users\KAVIYA\Downloads\sih2026_tarang_new_me\sih2026_tarang_new-main')
from dotenv import load_dotenv; load_dotenv()
import supabase_service as s

print('is_offshore_coordinate tests:')
print('  10.01, 80.015 ->', s.is_offshore_coordinate(10.01, 80.015))
print('  10.02, 80.005 ->', s.is_offshore_coordinate(10.02, 80.005))
print('  9.995, 79.990 ->', s.is_offshore_coordinate(9.995, 79.990))

DEMO_SURVEY = '6d17c69e-6d2c-5e13-8584-627bc50e9453'
print('\nGetting detections for demo survey...')
dets = s.get_all_detections(survey_id=DEMO_SURVEY)
print('Got', len(dets), 'detections')
for d in dets:
    det_id = d.get('id', 'N/A')
    lat = d.get('latitude')
    lon = d.get('longitude')
    off = d.get('is_offshore')
    rev = d.get('review_status')
    print(' ', det_id, '| lat=', lat, '| lon=', lon, '| is_offshore=', off, '| review=', rev)
