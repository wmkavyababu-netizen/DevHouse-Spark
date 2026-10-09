import sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')

r = requests.post('http://127.0.0.1:3000/api/auth/demo-access', json={'portal':'survey_operator'}, timeout=10)
token = r.json().get('token','')
headers = {'Authorization': 'Bearer ' + token}

SURVEY = '6d17c69e-6d2c-5e13-8584-627bc50e9453'
r2 = requests.get('http://127.0.0.1:3000/api/v1/surveys/' + SURVEY + '/detections', headers=headers, timeout=15)
dets = r2.json()
print('Total detections:', len(dets))
for d in dets[:6]:
    print('---')
    print('  ID:', d.get('id'))
    print('  class:', d.get('class_name'))
    print('  evidence_image_id:', d.get('evidence_image_id'))
    print('  evidence_image_url:', d.get('evidence_image_url'))
    print('  crop_url:', d.get('crop_url'))
    print('  image_url:', d.get('image_url'))
    print('  title:', d.get('title'))

# Also check survey images endpoint
print('\n=== Survey images ===')
r3 = requests.get('http://127.0.0.1:3000/api/v1/surveys/' + SURVEY + '/images', headers=headers, timeout=15)
imgs = r3.json()
print('Images:', json.dumps(imgs, indent=2)[:500])
