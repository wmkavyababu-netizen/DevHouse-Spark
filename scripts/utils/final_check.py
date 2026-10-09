import sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')
BASE = 'http://127.0.0.1:3000'

# Test simulation-data endpoint directly (no auth needed)
DEMO_ID = 'DET-FFF7EAD064AC'
print('=== Simulation data endpoint (no auth) ===')
r = requests.get(f'{BASE}/api/v1/simulation-data/{DEMO_ID}', timeout=15)
print('Status:', r.status_code)
print('Content-Type:', r.headers.get('Content-Type'))
print('Body (first 300):', r.text[:300])

print('\n=== Public stats ===')
r = requests.get(f'{BASE}/api/v1/stats/public', timeout=15)
print('Status:', r.status_code)
d = r.json()
print('surveys_completed:', d.get('surveys_completed'))
print('total_debris_detected:', d.get('total_debris_detected'))
print('summary.verified:', d.get('summary', {}).get('verified'))
