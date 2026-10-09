import sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')
token = open('token.tmp').read().strip()
headers = {'Authorization': 'Bearer ' + token}
r = requests.get('http://127.0.0.1:3000/api/v1/hotspot-route/latest', headers=headers, timeout=10)
print('Status:', r.status_code)
d = r.json()
if 'route' in d:
    route = d['route']
    print('Route ID:', route.get('route_id'))
    print('Start point:', route.get('start_point'))
    for l in route.get('legs', []):
        print('Leg', l.get('sequence'), ':', l.get('from'), '->', l.get('to'), '=', l.get('distance_nm'), 'NM (', l.get('distance_km'), 'km)')
    print('TOTAL:', route.get('total_distance_nm'), 'NM')
else:
    print(json.dumps(d, indent=2)[:600])
