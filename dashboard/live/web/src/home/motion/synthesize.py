#!/usr/bin/env python3
"""Google Cloud TTS. Set GOOGLE_CLOUD_QUOTA_PROJECT to an authorized project."""
import base64,json,os,subprocess,urllib.request
from pathlib import Path
p=Path(__file__).resolve().parent
project=os.environ['GOOGLE_CLOUD_QUOTA_PROJECT']
token=subprocess.check_output(['gcloud','auth','application-default','print-access-token'],text=True).strip()
for i,text in enumerate(json.loads((p/'narration.json').read_text()),1):
 data=json.dumps({'input':{'text':text},'voice':{'languageCode':'en-US','name':'en-US-Chirp3-HD-Enceladus'},'audioConfig':{'audioEncoding':'MP3','speakingRate':1.0}}).encode()
 req=urllib.request.Request('https://texttospeech.googleapis.com/v1/text:synthesize',data=data,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','x-goog-user-project':project})
 with urllib.request.urlopen(req) as response: audio=json.load(response)['audioContent']
 (p/f'assets/narration/{i}.mp3').write_bytes(base64.b64decode(audio))
