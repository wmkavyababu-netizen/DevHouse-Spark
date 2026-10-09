import sys, requests
sys.stdout.reconfigure(encoding='utf-8')
BASE = 'http://127.0.0.1:3000'
DEMO_SURVEY = '6d17c69e-6d2c-5e13-8584-627bc50e9453'

def get_token(portal):
    r = requests.post(BASE + '/api/auth/demo-access', json={'portal': portal}, timeout=10)
    if r.ok:
        return r.json().get('access_token', '')
    print('  [AUTH FAIL]', portal, r.status_code, r.text[:100])
    return ''

op_tok = get_token('survey_operator')
sa_tok = get_token('sonar_analyst')
ma_tok = get_token('marine_portal')
ga_tok = get_token('government_portal')

PASS = '[PASS]'
FAIL = '[FAIL]'
WARN = '[WARN]'

def check(label, r, ok_statuses=(200,)):
    icon = PASS if r.status_code in ok_statuses else FAIL
    print(icon, label + ':', r.status_code)
    return r.status_code in ok_statuses

print('=== TARANG E2E TEST ===')

# 1 — Detections (offshore fix)
print('\n[1] DETECTIONS + is_offshore check')
H = {'Authorization': 'Bearer ' + op_tok}
r = requests.get(BASE + '/api/v1/surveys/' + DEMO_SURVEY + '/detections', headers=H, timeout=15)
if check('GET detections', r):
    dets = r.json()
    v = [d for d in dets if (d.get('review_status') or '').lower() == 'verified']
    o = [d for d in dets if d.get('is_offshore')]
    print('  total=%d verified=%d offshore=%d' % (len(dets), len(v), len(o)))
    if len(o) < len(dets):
        print(WARN, 'is_offshore still False for', len(dets)-len(o), 'detections')
    else:
        print(PASS, 'All detections marked offshore')

# 2 — Hotspots
print('\n[2] HOTSPOTS (DBSCAN, marine_portal role)')
H2 = {'Authorization': 'Bearer ' + ma_tok}
r = requests.get(BASE + '/api/v1/hotspots', headers=H2, timeout=20)
if check('GET hotspots', r):
    hs = r.json()
    print('  count=%d' % len(hs))
    for h in hs:
        print('  ', h.get('id', 'N/A')[:20], 'targets=', h.get('total_targets'), 'lat=', h.get('latitude'), 'lon=', h.get('longitude'))
    print(PASS if len(hs) >= 2 else WARN, '2+ hotspots:', len(hs) >= 2)

# 3 — TSP (marine_portal role)
print('\n[3] TSP ROUTE OPTIMIZE')
r = requests.post(BASE + '/api/v1/routes/optimize', json={'survey_id': DEMO_SURVEY}, headers=H2, timeout=20)
if check('POST routes/optimize', r):
    rt = r.json().get('route') or {}
    print('  route_id=%s targets=%s dist=%s km' % (rt.get('route_id', 'N/A')[:20], rt.get('target_count'), rt.get('distance_km')))

# 4 — Hotspot route latest (gov portal)
print('\n[4] GOV PORTAL: HOTSPOT ROUTE LATEST')
H4 = {'Authorization': 'Bearer ' + ga_tok}
r = requests.get(BASE + '/api/v1/hotspot-route/latest', headers=H4, timeout=10)
if check('GET hotspot-route/latest', r):
    d = r.json()
    rt = d.get('route') or {}
    print('  status=%s route_id=%s hotspots=%s dist=%s NM' % (d.get('status'), rt.get('route_id', 'N/A'), rt.get('hotspot_count'), rt.get('total_distance_nm')))

# 5 — Gov hotspot-route POST (generate new)
print('\n[5] GOV PORTAL: GENERATE NEW HOTSPOT ROUTE')
r = requests.post(BASE + '/api/v1/hotspot-route', json={}, headers=H4, timeout=20)
if check('POST hotspot-route', r, ok_statuses=(200, 409)):
    d = r.json()
    if r.status_code == 200:
        rt = d.get('route') or {}
        print('  route_id=%s hotspots=%s dist=%s NM' % (rt.get('route_id','N/A'), rt.get('hotspot_count'), rt.get('total_distance_nm')))
    else:
        print('  409 msg:', d.get('message', ''))

# 6 — Clearance
print('\n[6] CLEARANCE')
r = requests.get(BASE + '/api/v1/clearance', headers=H2, timeout=10)
check('GET clearance', r)
if r.ok:
    items = r.json()
    print('  count=%d' % len(items))

# 7 — Public stats
print('\n[7] PUBLIC STATS')
r = requests.get(BASE + '/api/v1/stats/public', timeout=10)
if check('GET stats/public', r):
    s = r.json().get('summary', {})
    print('  total=%d verified=%d hotspots=%d' % (s.get('total',0), s.get('verified',0), s.get('hotspot_count',0)))

# 8 — Survey create (survey_operator)
print('\n[8] SURVEY CREATION (existing survey upsert)')
r = requests.post(BASE + '/api/v1/surveys', json={
    'survey_id': DEMO_SURVEY,
    'survey_name': 'Test Upsert',
    'created_by': 'test'
}, headers={'Authorization': 'Bearer ' + op_tok, 'Content-Type': 'application/json'}, timeout=10)
check('POST surveys (duplicate should succeed)', r, ok_statuses=(200, 201))
if r.ok:
    print('  survey_id:', r.json().get('survey_id', 'N/A'))

print('\n=== DONE ===')
