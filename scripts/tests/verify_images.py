import sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')
BASE = 'http://127.0.0.1:3000'
SURVEY = '6d17c69e-6d2c-5e13-8584-627bc50e9453'

r = requests.post(f'{BASE}/api/auth/demo-access', json={'portal':'survey_operator'}, timeout=10)
token = r.json().get('access_token','')  # FIELD IS access_token NOT token
headers = {'Authorization': 'Bearer ' + token}

print('=== Detection image URLs ===')
r2 = requests.get(f'{BASE}/api/v1/surveys/{SURVEY}/detections', headers=headers, timeout=15)
dets = r2.json() if isinstance(r2.json(), list) else []
print(f'Detections: {len(dets)}')
for d in dets:
    cid = d.get('id','')
    cls = d.get('class_name','')
    cu  = d.get('crop_url','') or ''
    eu  = d.get('evidence_image_url','') or ''
    print(f'  {cid} | {cls}')
    print(f'    crop_url: {cu[:100]}')
    print(f'    evidence_image_url: {eu[:100]}')

print('\n=== Survey images via /xtf/<id>/images ===')
# Use sonar_analyst token for this endpoint
r_sa = requests.post(f'{BASE}/api/auth/demo-access', json={'portal':'sonar_analyst'}, timeout=10)
token_sa = r_sa.json().get('access_token','')
headers_sa = {'Authorization': 'Bearer ' + token_sa}
r3 = requests.get(f'{BASE}/api/v1/xtf/{SURVEY}/images', headers=headers_sa, timeout=15)
print('Status:', r3.status_code)
imgs = r3.json()
if isinstance(imgs, list):
    for img in imgs:
        print(f"  seq={img.get('sequence')} image_id={img.get('image_id','')} url={img.get('url','')[:90]}")
else:
    print(json.dumps(imgs)[:300])

print('\n=== Test first image is accessible ===')
if isinstance(imgs, list) and imgs:
    url = imgs[0].get('url','')
    if url.startswith('https://'):
        rimg = requests.head(url, timeout=10)
        print(f'HEAD {url[:80]}: {rimg.status_code} {rimg.headers.get("Content-Type","")}')
    elif url.startswith('/'):
        rimg = requests.get(BASE + url, timeout=10)
        print(f'GET /outputs/...: {rimg.status_code} {rimg.headers.get("Content-Type","")} {rimg.headers.get("Content-Length","")}B')
