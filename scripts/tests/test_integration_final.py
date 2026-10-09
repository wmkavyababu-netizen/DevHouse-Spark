"""TARANG final integration tests — run against the live server at :3000."""
import sys, requests, json, time
sys.stdout.reconfigure(encoding='utf-8')
BASE = 'http://127.0.0.1:3000'

PASS = '\u2705'; FAIL = '\u274c'

def check(label, ok, detail=''):
    icon = PASS if ok else FAIL
    print(f'{icon}  {label}' + (f'  [{detail}]' if detail else ''))
    return ok

# ---------- 1. AI Chat ----------
print('\n=== 1. TARANG AI CHAT ===')
try:
    r = requests.post(f'{BASE}/api/v1/chat', json={'message': 'What is TARANG in one sentence?'}, timeout=25)
    reply = r.json().get('reply', '')
    ai_ok = r.status_code == 200 and 'trouble connecting' not in reply
    check('AI chat responds without error', ai_ok, reply[:100])
except Exception as e:
    check('AI chat responds', False, str(e))

# ---------- 2. Public stats ----------
print('\n=== 2. PUBLIC STATS ===')
try:
    r = requests.get(f'{BASE}/api/v1/stats/public', timeout=10)
    d = r.json()
    check('API returns surveys_completed', d.get('surveys_completed') is not None, str(d.get('surveys_completed')))
    check('API returns total_debris_detected', d.get('total_debris_detected') is not None, str(d.get('total_debris_detected')))
    check('API returns summary.verified', d.get('summary',{}).get('verified') is not None)
except Exception as e:
    check('Public stats API', False, str(e))

# ---------- 3. Simulation data endpoint ----------
print('\n=== 3. SIMULATION DATA ENDPOINT ===')
DEMO_ID = 'DET-FFF7EAD064AC'
try:
    r = requests.get(f'{BASE}/api/v1/simulation-data/{DEMO_ID}', timeout=10)
    d = r.json()
    check('Endpoint returns 200', r.status_code == 200, str(r.status_code))
    check('schemaVersion=1', d.get('schemaVersion') == 1)
    check('source=survey', d.get('source') == 'survey')
    check('Has trajectory', len(d.get('trajectory', [])) > 0)
    check('Has 1 detection', len(d.get('detections', [])) == 1)
    det = d['detections'][0] if d.get('detections') else {}
    check('Detection ID matches', det.get('id') == DEMO_ID, det.get('id'))
    check('Has confidence', det.get('confidence') is not None, str(det.get('confidence')))
    check('Has position', det.get('position') is not None)
    check('Has shadow data', det.get('shadow') is not None)
except Exception as e:
    check('Simulation data endpoint', False, str(e))

# ---------- 4. Detections for demo survey ----------
print('\n=== 4. DETECTIONS ===')
DEMO_SURVEY = '6d17c69e-6d2c-5e13-8584-627bc50e9453'
try:
    # Get a token
    auth = requests.post(f'{BASE}/api/auth/demo-access', json={'portal': 'survey_operator'}, timeout=10)
    token = auth.json().get('token', '')
    headers = {'Authorization': f'Bearer {token}'}
    
    r = requests.get(f'{BASE}/api/v1/surveys/{DEMO_SURVEY}/detections', headers=headers, timeout=10)
    dets = r.json()
    check('Detections API returns list', isinstance(dets, list), f'{len(dets)} items')
    if dets:
        d0 = dets[0]
        check('Detection has lat/lon', d0.get('latitude') and d0.get('longitude'))
        check('Lat in valid range (not flipped)', 0 < float(d0.get('latitude', 0)) < 90)
        check('Detection has confidence', d0.get('confidence') is not None)
        check('Detection has id', d0.get('id') is not None)
except Exception as e:
    check('Detections API', False, str(e))

# ---------- 5. Hotspot route ----------
print('\n=== 5. HOTSPOT ROUTE ===')
try:
    r = requests.get(f'{BASE}/api/v1/hotspot-route/latest', headers=headers, timeout=10)
    d = r.json()
    if 'route' in d:
        route = d['route']
        check('Route exists', True, route.get('route_id'))
        check('Has legs', len(route.get('legs', [])) > 0)
        check('Legs have distance_nm', all(l.get('distance_nm') is not None for l in route.get('legs', [])))
        check('Total distance >0', route.get('total_distance_nm', 0) > 0, str(route.get('total_distance_nm')))
        # Check no duplicate total distance bug
        legs = route.get('legs', [])
        if len(legs) >= 2:
            distinct = len(set(l['distance_nm'] for l in legs))
            check('Leg distances are varied (not all same)', distinct > 1 or len(legs) < 2, f'{distinct} distinct values')
    else:
        check('Route data present', False, str(d)[:100])
except Exception as e:
    check('Hotspot route API', False, str(e))

print('\n=== ALL TESTS COMPLETE ===')
