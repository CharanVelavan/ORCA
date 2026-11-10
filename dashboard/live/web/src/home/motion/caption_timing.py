#!/usr/bin/env python3
"""Align the approved narration words to local Whisper word timestamps.

Build-only dependency: faster-whisper. No model is needed by the dashboard.
ASR text supplies timing; the approved narration remains the displayed text.
"""
from pathlib import Path
from difflib import SequenceMatcher
import argparse
import json
import re
import subprocess
import numpy as np
from faster_whisper import WhisperModel

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--model', default='base.en')
parser.add_argument('--cache', default='/private/tmp/orca-captions-model')
args = parser.parse_args()
model = WhisperModel(args.model, device='cpu', compute_type='int8', cpu_threads=4, download_root=args.cache)
texts = json.loads((root / 'narration.json').read_text())
html = (root / 'index.html').read_text()
names = ['story','incident','models','policy','approval','ending']
starts = [float(re.search(r'id="'+n+r'"[^>]*data-start="([\d.]+)"', html)[1]) + .3 for n in names]
norm = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
words = []
reports = []
for number, (text, offset) in enumerate(zip(texts, starts), 1):
    audio = root / f'assets/narration/{number}.mp3'
    duration = float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(audio)], text=True))
    pcm = subprocess.check_output(['ffmpeg','-v','error','-i',str(audio),'-f','f32le','-ac','1','-ar','16000','pipe:1'])
    samples = np.frombuffer(pcm,dtype='<f4')
    segments, _ = model.transcribe(samples, language='en', beam_size=5, word_timestamps=True, condition_on_previous_text=False, initial_prompt=text, vad_filter=False)
    heard = [dict(text=w.word.strip(), start=w.start, end=w.end) for segment in segments for w in (segment.words or []) if norm(w.word)]
    reference = text.split()
    ref = [norm(w) for w in reference]
    hyp = [norm(w['text']) for w in heard]
    matcher = SequenceMatcher(None, ref, hyp, autojunk=False)
    aligned = [None] * len(reference)
    for operation, a, b, c, d in matcher.get_opcodes():
        if operation == 'insert':
            continue
        if operation == 'equal':
            for i, j in zip(range(a,b),range(c,d)):
                aligned[i] = (heard[j]['start'], heard[j]['end'])
        else:
            begin = heard[c]['start'] if c < len(heard) else (heard[-1]['end'] if heard else 0)
            end = heard[d-1]['end'] if d > c else (heard[c]['start'] if c < len(heard) else duration)
            if end <= begin:
                begin = heard[c-1]['end'] if c else 0
                end = heard[c]['start'] if c < len(heard) else duration
            length = max(.02 * (b-a), end-begin)
            weights = [max(1,len(w)) for w in reference[a:b]]
            cursor = begin
            for i, weight in zip(range(a,b), weights):
                stop = cursor + length * weight / sum(weights)
                aligned[i] = (cursor, min(duration,stop))
                cursor = stop
    previous = 0
    for i, (word, times) in enumerate(zip(reference, aligned)):
        begin, end = times
        begin = min(duration, max(previous, begin))
        end = min(duration, max(begin + .025, end))
        words.append({'text':word, 'start':round(offset+begin,3), 'end':round(offset+end,3), 'scene':number})
        previous = end
    reports.append({'scene':number,'similarity':round(matcher.ratio(),4),'approved':text,'recognized':' '.join(w['text'] for w in heard),'asr_words':heard})
    print(f'Scene {number}: {len(reference)} approved words, alignment similarity {matcher.ratio():.3f}', flush=True)
(root / 'assets/caption-words.json').write_text(json.dumps(words,indent=2)+'\n')
(root / 'assets/caption-alignment.json').write_text(json.dumps(reports,indent=2)+'\n')
