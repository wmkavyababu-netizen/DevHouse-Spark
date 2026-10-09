"""TARANG Gemini connectivity test.

Reads GEMINI_API_KEY from the project .env file via python-dotenv.
NEVER hardcode the key here — keep it in .env only.

Usage:
    python test_gemini.py
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()  # loads from .env in the current directory

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

if not GEMINI_API_KEY:
    print("[ERROR] GEMINI_API_KEY is not set. Add it to your .env file.")
    raise SystemExit(1)

# gemini-3.8-flash: confirmed available on this key via ListModels.
MODEL = 'gemini-3.8-flash'
URL   = f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={GEMINI_API_KEY}'

payload = {
    'contents': [{'parts': [{'text': 'What is marine debris detection?'}]}],
    'systemInstruction': {
        'parts': [{
            'text': (
                'You are TARANG AI, an assistant for the TARANG Unified Maritime AI Platform. '
                'Answer questions about marine debris, underwater sonar (XTF), side-scan sonar, '
                'AUV surveys, cleanup missions, AI detection, hotspot mapping, '
                'and Indian Ocean operations. Keep answers concise and domain-accurate.'
            )
        }]
    }
}

try:
    resp = requests.post(URL, json=payload, timeout=15)
    data = resp.json()
    print('Status:', resp.status_code)
    if 'error' in data:
        print('API Error:', data['error'].get('message', 'Unknown error'))
    elif 'candidates' in data:
        reply = data['candidates'][0]['content']['parts'][0]['text']
        print('Reply:', reply[:500])
    else:
        print('Unexpected response shape:', list(data.keys()))
except Exception as e:
    print('Request failed:', e)
