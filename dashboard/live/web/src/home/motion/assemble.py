#!/usr/bin/env python3
"""Mix 4K HyperFrames, native 4K 3D shots, narration and ducked effects."""
from pathlib import Path
import json,re,subprocess
p=Path(__file__).resolve().parent
media=(p/'../../../public/media').resolve()
visual=media/'orca-method-4k-visual.mp4'; output=media/'orca-method-4k.mp4'
names=['story','incident','models','policy','approval','ending']
html=(p/'index.html').read_text()
def timing(name,key):
 return float(re.search(r'id="'+name+r'"[^>]*data-'+key+r'="([\d.]+)"',html)[1])
scene_starts=[timing(n,'start') for n in names]
scene_lengths=[timing(n,'duration') for n in names]
starts=[x+.3 for x in scene_starts];total=scene_starts[-1]+scene_lengths[-1]
voices=[p/f'assets/narration/{i}.mp3' for i in range(1,7)]
def duration(path):
 return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(path)],text=True))
lengths=[duration(f) for f in voices]
for i,(start,length,end) in enumerate(zip(starts,lengths,[a+b for a,b in zip(scene_starts,scene_lengths)]),1):
 if start+length>end: raise SystemExit(f'Narration {i} does not fit its scene: {start+length:.3f} > {end:.3f}')
shots=[p/'assets/normal-4k.mp4',p/'assets/attack-4k.mp4',p/'assets/recovery-4k.mp4']
cmd=['ffmpeg','-v','error','-y','-i',str(visual)]
for shot in shots: cmd+=['-stream_loop','-1','-i',str(shot)]
for voice in voices: cmd+=['-i',str(voice)]
cmd+=['-i',str(p/'assets/sound-effects.flac'),'-loop','1','-i',str(p/'assets/brand-mark.png')]
filters=['[1:v]scale=2220:1248[normal]','[2:v]scale=2220:1248[attack]','[3:v]scale=2220:1248[recovery]',f"[0:v][normal]overlay=1440:690:enable='between(t,0,{scene_starts[1]})'[v1]",f"[v1][attack]overlay=1440:690:enable='between(t,{scene_starts[1]},{scene_starts[2]})'[v2]",f"[v2][recovery]overlay=1440:690:enable='between(t,{scene_starts[4]},{total})'[v3]",'[v3][11:v]overlay=105:189:shortest=1[v]']
for i,t in enumerate(starts): filters.append(f'[{i+4}:a]aformat=channel_layouts=stereo,adelay={round(t*1000)}|{round(t*1000)}[a{i}]')
filters.append(''.join(f'[a{i}]' for i in range(6)) + f'amix=inputs=6:duration=longest:normalize=0,apad=whole_dur={total},asplit=2[voice][key]')
filters += ['[10:a]volume=0.65[effects]', '[effects][key]sidechaincompress=threshold=0.025:ratio=5:attack=20:release=250[ducked]', '[voice][ducked]amix=inputs=2:duration=first:normalize=0,volume=4dB[a]']
cmd+=['-filter_complex',';'.join(filters),'-map','[v]','-map','[a]','-t',str(total),'-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(output)]
subprocess.run(cmd,check=True)
subprocess.run(['ffmpeg','-v','error','-y','-i',str(output),'-vf','scale=1280:720:flags=lanczos','-c:v','libx264','-preset','veryfast','-crf','21','-c:a','copy','-movflags','+faststart',str(media/'orca-method.mp4')],check=True)
subprocess.run(['ffmpeg','-v','error','-y','-ss','1','-i',str(output),'-frames:v','1','-vf','scale=1280:720','-q:v','3',str(media/'orca-method-poster.jpg')],check=True)
texts=json.loads((p/'narration.json').read_text())
def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02}.{ms%1000:03}'
cues=['WEBVTT','']
for text,start,length in zip(texts,starts,lengths):
 sentences=[s.strip() for s in re.split(r'(?<=[.!?])\s+',text) if s.strip()]; chars=sum(len(s) for s in sentences); cur=start
 for i,s in enumerate(sentences):
  end=start+length if i==len(sentences)-1 else cur+length*len(s)/chars
  cues += [f'{stamp(cur)} --> {stamp(end)}',s,''];cur=end
(media/'orca-method.vtt').write_text('\n'.join(cues))
print('Narration durations:', ', '.join(f'{x:.3f}s' for x in lengths))
