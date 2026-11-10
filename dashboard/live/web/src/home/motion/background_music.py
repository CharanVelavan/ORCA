#!/usr/bin/env python3
"""Render an original, deterministic instrumental bed (NumPy + ffmpeg)."""
from pathlib import Path
import math, re, subprocess, tempfile, wave
import numpy as np

ROOT = Path(__file__).resolve().parent
RATE = 48000
html = (ROOT / 'index.html').read_text()
DURATION = float(re.search(r'data-composition-id="main"[^>]*data-duration="([\d.]+)"', html)[1])
n = round(DURATION * RATE)
left = np.zeros(n, dtype=np.float32)
right = np.zeros(n, dtype=np.float32)
# A minor → F major → C major → G major, with a restrained open voicing.
chords = [(57, 60, 64, 69), (53, 57, 60, 65), (48, 55, 60, 64), (55, 59, 62, 67)]
def freq(note): return 440.0 * 2 ** ((note - 69) / 12)
def add_pad(start, notes):
    length = 7.55
    a = round(start * RATE); b = min(n, round((start + length) * RATE))
    if b <= a: return
    t = np.arange(b - a, dtype=np.float32) / RATE
    env = np.minimum(1, t / 1.15) * np.minimum(1, np.maximum(0, (length - t) / 1.15))
    for idx, note in enumerate(notes):
        f = freq(note); pan = (-.55, .35, -.25, .55)[idx]
        # Soft upper partials, no bright transient or percussion.
        wave_l = np.sin(2 * np.pi * f * t) + .18 * np.sin(4 * np.pi * f * t)
        wave_r = np.sin(2 * np.pi * f * 1.0015 * t) + .18 * np.sin(4 * np.pi * f * 1.0015 * t)
        left[a:b] += wave_l * env * (.62 - .22 * pan)
        right[a:b] += wave_r * env * (.62 + .22 * pan)
def add_note(start, note, pan):
    length = 1.3; a = round(start * RATE); b = min(n, round((start + length) * RATE))
    if b <= a: return
    t = np.arange(b-a, dtype=np.float32) / RATE
    env = np.minimum(1, t/.08) * np.exp(-t*2.8)
    f = freq(note)
    tone = np.sin(2*np.pi*f*t) + .12*np.sin(4*np.pi*f*t)
    left[a:b] += tone * env * (.25 - .12*pan)
    right[a:b] += tone * env * (.25 + .12*pan)
bar = 60/72*8
for k in range(math.ceil(DURATION/bar)):
    add_pad(k*bar, chords[k % len(chords)])
# Eight-note arpeggio; soft and sparse enough to leave narration clear.
beat = 60/72
pattern = (0, 2, 3, 2, 1, 2, 3, 2)
for k in range(math.ceil(DURATION/beat)):
    chord = chords[int(k//8) % len(chords)]
    add_note(k*beat + .15, chord[pattern[k%8]] + 12, (-.45, .45)[k%2])
# Smooth opening and closing, with a predictable -15 dBFS peak master.
t = np.arange(n, dtype=np.float32) / RATE
envelope = np.minimum(1, t/3) * np.minimum(1, np.maximum(0, (DURATION-t)/5))
left *= envelope; right *= envelope
peak = max(float(np.max(np.abs(left))), float(np.max(np.abs(right))))
scale = .178 / peak
stereo = np.empty((n, 2), dtype='<i2')
stereo[:,0] = np.clip(left * scale * 32767, -32768, 32767).astype('<i2')
stereo[:,1] = np.clip(right * scale * 32767, -32768, 32767).astype('<i2')
output = ROOT/'assets'/'background-music.flac'
with tempfile.TemporaryDirectory(prefix='orca-music-') as tmp:
    wav = Path(tmp)/'music.wav'
    with wave.open(str(wav),'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(stereo.tobytes())
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(wav),'-c:a','flac',str(output)],check=True)
print(f'Wrote {output.name}, {DURATION:g}s, 48 kHz stereo; peak target −15 dBFS')
