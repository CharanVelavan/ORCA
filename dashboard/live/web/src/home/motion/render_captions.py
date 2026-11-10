#!/usr/bin/env python3
"""Create a small transparent 4K caption strip with a highlighted spoken word."""
from pathlib import Path
import argparse
import json
import re
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--out', default='/private/tmp/orca-live-captions')
args = parser.parse_args()
output = Path(args.out)
output.mkdir(parents=True, exist_ok=True)
font_path = root / 'assets/fonts/geist-800.ttf'
if not font_path.exists():
    font = TTFont(root / 'assets/fonts/geist-800.woff2')
    font.flavor = None
    font.save(font_path)
font = ImageFont.truetype(str(font_path), 62)
words = json.loads((root / 'assets/caption-words.json').read_text())
html = (root / 'index.html').read_text()
total = float(re.search(r'data-composition-id="main"[^>]*data-duration="([\d.]+)"', html)[1])
phrases = []
current = []
for word in words:
    if current and (word['scene'] != current[-1]['scene'] or len(current) >= 6 or sum(len(w['text'])+1 for w in current)+len(word['text']) > 46):
        phrases.append(current)
        current = []
    current.append(word)
    if re.search(r'[.!?]$', word['text']):
        phrases.append(current)
        current = []
if current:
    phrases.append(current)
width, height = 3840, 140
blank = output / 'blank.png'
Image.new('RGBA', (width,height)).save(blank)
events = [{'at':0.0, 'file':blank.name}]
cues = []
for number, phrase in enumerate(phrases):
    next_start = phrases[number+1][0]['start'] if number+1 < len(phrases) else total
    start = max(0, phrase[0]['start']-.03)
    end = min(next_start-.03, phrase[-1]['end']+.12, total)
    text = ' '.join(w['text'] for w in phrase)
    cues.append({'start':round(start,3),'end':round(end,3),'text':text})
    measure = ImageDraw.Draw(Image.new('RGBA',(1,1)))
    space = measure.textlength(' ',font=font)
    lengths = [measure.textlength(w['text'],font=font) for w in phrase]
    full = sum(lengths)+space*(len(lengths)-1)
    left = (width-full)/2
    for index, word in enumerate(phrase):
        image = Image.new('RGBA',(width,height))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((left-32,14,left+full+32,118),radius=8,fill=(17,17,17,246))
        x = left
        for j, (item, length) in enumerate(zip(phrase,lengths)):
            if j == index:
                draw.rounded_rectangle((x-8,25,x+length+8,106),radius=5,fill=(109,0,26,255))
            draw.text((x,66),item['text'],font=font,anchor='lm',fill=(255,255,255,255) if j==index else (232,232,232,255))
            x += length+space
        file = f'phrase-{number:03}-word-{index:02}.png'
        image.save(output / file)
        events.append({'at':start if index==0 else word['start'], 'file':file})
    events.append({'at':end, 'file':blank.name})
assert all(0 <= cue['start'] < cue['end'] <= total for cue in cues)
assert all(cues[i]['end'] <= cues[i+1]['start'] for i in range(len(cues)-1))
assert ' '.join(cue['text'] for cue in cues) == ' '.join(json.loads((root/'narration.json').read_text()))
events.sort(key=lambda e:e['at'])
lines = ['ffconcat version 1.0']
for i, event in enumerate(events):
    stop = events[i+1]['at'] if i+1 < len(events) else total
    if stop <= event['at']:
        continue
    lines += [f"file '{(output/event['file']).as_posix()}'",f"duration {stop-event['at']:.6f}"]
lines.append(f"file '{blank.as_posix()}'")
(output/'captions.ffconcat').write_text('\n'.join(lines)+'\n')
(root/'assets/caption-phrases.json').write_text(json.dumps(cues,indent=2)+'\n')

def stamp(t):
    value=round(t*1000)
    return f'{value//3600000:02}:{value//60000%60:02}:{value//1000%60:02}.{value%1000:03}'
vtt=['WEBVTT','']
for cue in cues:
    vtt += [f"{stamp(cue['start'])} --> {stamp(cue['end'])}",cue['text'],'']
(root/'../../../public/media/orca-method.vtt').resolve().write_text('\n'.join(vtt))
print(f'{len(words)} approved words, {len(cues)} caption phrases, {len(events)} display states',flush=True)
