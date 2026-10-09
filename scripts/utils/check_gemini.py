import sys, requests, os
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv; load_dotenv()
key = os.environ.get('GEMINI_API_KEY','')
print('Key length:', len(key))

# Try v1beta
for ver in ['v1beta', 'v1']:
    for model in ['gemini-2.5-flash', 'gemini-flash-latest', 'gemini-2.0-flash-001']:
        url = f'https://generativelanguage.googleapis.com/{ver}/models/{model}:generateContent?key={key}'
        payload = {'contents': [{'parts': [{'text': 'What is TARANG? One sentence.'}]}]}
        try:
            r = requests.post(url, json=payload, timeout=15)
            if r.ok:
                d = r.json()
                if 'candidates' in d:
                    print(f'SUCCESS: {ver}/{model}')
                    print('Reply:', d['candidates'][0]['content']['parts'][0]['text'][:100])
                    break
            else:
                d = r.json()
                print(f'FAIL {ver}/{model}: HTTP {r.status_code} - {d.get("error", {}).get("message","")[:80]}')
        except Exception as e:
            print(f'ERR {ver}/{model}: {e}')
