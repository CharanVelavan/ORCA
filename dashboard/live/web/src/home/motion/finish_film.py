#!/usr/bin/env python3
"""Add live-style captions, original music and independently ducked effects.

Consumes the clean 4K export and prepared caption PNG strip; never burns twice.
"""
from pathlib import Path
import argparse
import json
import re
import shutil
import subprocess

root = Path(__file__).resolve().parent
media = (root / '../../../public/media').resolve()
parser = argparse.ArgumentParser()
parser.add_argument('--refresh-clean', action='store_true', help='Use a newly rendered, uncaptioned 4K export as the clean base.')
args = parser.parse_args()
clean = root / 'assets/film-clean-4k.mp4'
if args.refresh_clean or not clean.exists():
    shutil.copy2(media / 'orca-method-4k.mp4', clean)
html = (root / 'index.html').read_text()
names = ['story','incident','models','policy','approval','ending']
starts = [float(re.search(r'id="'+name+r'"[^>]*data-start="([\d.]+)"',html)[1])+.3 for name in names]
total = float(re.search(r'data-composition-id="main"[^>]*data-duration="([\d.]+)"',html)[1])
master = media / 'orca-method-4k-next.mp4'
web = media / 'orca-method-next.mp4'
poster = media / 'orca-method-poster-next.jpg'
cmd = ['ffmpeg','-v','error','-y','-i',str(clean),'-f','concat','-safe','0','-i','/private/tmp/orca-live-captions/captions.ffconcat']
for index in range(1,7):
    cmd += ['-i',str(root/f'assets/narration/{index}.mp3')]
cmd += ['-i',str(root/'assets/sound-effects.flac'),'-i',str(root/'assets/background-music.flac')]
filters = ['[0:v][1:v]overlay=0:2020:format=auto:eof_action=pass[v]']
for i,start in enumerate(starts):
    filters.append(f'[{i+2}:a]aformat=channel_layouts=stereo,adelay={round(start*1000)}|{round(start*1000)}[a{i}]')
filters += [
    ''.join(f'[a{i}]' for i in range(6))+f'amix=inputs=6:duration=longest:normalize=0,apad=whole_dur={total},asplit=3[voice][effects-key][music-key]',
    '[8:a]volume=0.65[effects]',
    '[effects][effects-key]sidechaincompress=threshold=0.025:ratio=5:attack=20:release=250[effects-ducked]',
    '[9:a]volume=0.16[music]',
    '[music][music-key]sidechaincompress=threshold=0.02:ratio=4:attack=50:release=400[music-ducked]',
    '[voice][effects-ducked][music-ducked]amix=inputs=3:duration=first:normalize=0,volume=4dB,alimiter=limit=0.89:level=0[a]',
]
cmd += ['-filter_complex',';'.join(filters),'-map','[v]','-map','[a]','-t',str(total),'-r','24','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','-progress','/private/tmp/orca-caption-progress.txt',str(master)]
subprocess.run(cmd,check=True)
subprocess.run(['ffmpeg','-v','error','-y','-i',str(master),'-vf','scale=1280:720:flags=lanczos','-c:v','libx264','-preset','veryfast','-crf','21','-c:a','copy','-movflags','+faststart',str(web)],check=True)
subprocess.run(['ffmpeg','-v','error','-y','-ss','2','-i',str(master),'-frames:v','1','-vf','scale=1280:720','-q:v','3',str(poster)],check=True)
for path, width, height in [(master,3840,2160),(web,1280,720)]:
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],text=True))
    video=next(s for s in info['streams'] if s['codec_type']=='video')
    assert video['width']==width and video['height']==height
    assert abs(float(info['format']['duration'])-total)<.1
    assert any(s['codec_type']=='audio' for s in info['streams'])
master.replace(media/'orca-method-4k.mp4')
web.replace(media/'orca-method.mp4')
poster.replace(media/'orca-method-poster.jpg')
print('Published captioned 4K and HD film with music, narration and effects.',flush=True)
