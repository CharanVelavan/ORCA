#!/usr/bin/env python3
"""Create an original, quiet stereo effects bed; no downloaded audio or voices."""
from array import array
from pathlib import Path
import math
import random
import re
import wave
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
RATE = 48000
html = (ROOT / 'index.html').read_text()
duration = float(re.search(r'data-composition-id="main"[^>]*data-duration="([\d.]+)"', html)[1])
starts = {name: float(re.search(r'id="' + name + r'"[^>]*data-start="([\d.]+)"', html)[1]) for name in ['story', 'incident', 'models', 'policy', 'approval', 'ending']}
bed = array('f', [0]) * (round(duration * RATE) * 2)
rng = random.Random(1701)

def tone(at, seconds, frequencies, gain=.055, pan=0, sweep=0, noise=0):
    begin = round(at * RATE)
    count = round(seconds * RATE)
    for frame in range(count):
        t = frame / RATE
        phase = frame / max(1, count - 1)
        envelope = min(1, t / .012) * (1 - phase) ** 2
        sample = sum(math.sin(2 * math.pi * (f * t + sweep * t * t / 2)) for f in frequencies) / len(frequencies)
        sample = gain * envelope * ((1 - noise) * sample + noise * rng.uniform(-1, 1))
        pos = (begin + frame) * 2
        if pos + 1 < len(bed):
            bed[pos] += sample * math.sqrt((1 - pan) / 2)
            bed[pos + 1] += sample * math.sqrt((1 + pan) / 2)

# Satellite link acquisition and brief packet movement.
for n in range(4):
    tone(.9 + n * .42, .16, [660 + n * 110, 990 + n * 110], .045, -.6 + n * .4)
# A restrained two-pulse intrusion alert.
for n in range(2):
    tone(starts['incident'] + .3 + n * .32, .22, [185, 277], .065)
# Soft transition sweeps, followed by model and evidence cues.
for name in ['models', 'policy', 'approval', 'ending']:
    tone(max(0, starts[name] - .12), .3, [280], .035, sweep=1400, noise=.8)
for n in range(4):
    tone(starts['models'] + 1 + n * .3, .09, [550 + n * 90], .035, -.5 + n / 3)
tone(starts['policy'] + 1, .32, [440, 660], .035)
# Clone/approval and rollout acknowledgements stay below narration.
tone(starts['approval'] + .7, .16, [390, 585], .035)
for n in range(3):
    tone(starts['approval'] + 6 + n * 3, .14, [520 + n * 130], .04, -.3 + n * .3)
# Recovery resolves the alert rather than repeating a siren.
for n, freq in enumerate([523.25, 659.25, 783.99]):
    tone(starts['ending'] + .45 + n * .14, .65, [freq], .04, -.25 + n * .25)

output = ROOT / 'assets' / 'sound-effects.flac'
output.parent.mkdir(parents=True, exist_ok=True)
pcm = array('h', (round(max(-1, min(1, s)) * 32767) for s in bed))
import sys
if sys.byteorder != 'little': pcm.byteswap()
with tempfile.TemporaryDirectory(prefix='orca-sound-') as temp:
    intermediate = Path(temp) / 'sound-effects.wav'
    with wave.open(str(intermediate), 'wb') as file:
        file.setnchannels(2)
        file.setsampwidth(2)
        file.setframerate(RATE)
        file.writeframes(pcm.tobytes())
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(intermediate), '-c:a', 'flac', str(output)], check=True)
print(f'Generated {duration:g}s stereo effects bed: {output.name}')
