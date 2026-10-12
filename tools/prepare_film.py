"""Encode a forward/reverse loop from the client's 4K camera orbit.
The verified original is kept in the excluded local work folder; no uploads.
"""
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
IDENT='1aoRCMwcD4HQxn5Qil7uukMVkgXbDf1AP'
SOURCE=ROOT/'_media_work/originals'/f'{IDENT}.mp4'
OUT=ROOT/'assets/media'
START=0.5
SOURCE_DURATION=8
FPS=24
SOURCE_FRAMES=round(SOURCE_DURATION*FPS)
LOOP_FRAMES=2*SOURCE_FRAMES-2
DURATION=LOOP_FRAMES/FPS

def verify_loop(target):
    # Compare decoded adjacent frames at both turnarounds with ordinary steps.
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(target),'-an','-vf','scale=64:36','-pix_fmt','gray','-f','rawvideo','-'])
    stride=64*36
    frames=[raw[i:i+stride] for i in range(0,len(raw),stride)]
    assert len(frames)==LOOP_FRAMES
    def delta(a,b):return sum(abs(x-y) for x,y in zip(frames[a],frames[b]))/stride
    result=dict(frames=len(frames),seam_delta=round(delta(-1,0),3),first_step_delta=round(delta(0,1),3),
                forward_turn_delta=round(delta(SOURCE_FRAMES-2,SOURCE_FRAMES-1),3),
                reverse_turn_delta=round(delta(SOURCE_FRAMES-1,SOURCE_FRAMES),3))
    assert result['seam_delta']<=result['first_step_delta']*1.5+1
    assert abs(result['forward_turn_delta']-result['reverse_turn_delta'])<1.5
    return result

def main():
    verified=json.loads(SOURCE.with_suffix('.mp4.verified.json').read_text(encoding='utf8'))
    assert SOURCE.stat().st_size==verified['bytes']
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==verified['sha256']
    outputs={}
    for name,width,crf,fps,rate in [('desktop',1920,20,FPS,'5500k'),('mobile',1280,21,FPS,'2000k')]:
        target=OUT/f'mrasi-alsaada-2-loop-{name}.mp4'
        filters=(f'[0:v]fps={fps},scale={width}:-2,format=yuv420p,trim=end_frame={SOURCE_FRAMES},setpts=PTS-STARTPTS,split[f][r];'
                 f'[r]reverse,trim=start_frame=1:end_frame={SOURCE_FRAMES-1},setpts=PTS-STARTPTS[back];'
                 '[f][back]concat=n=2:v=1:a=0[v]')
        subprocess.run(['ffmpeg','-v','error','-xerror','-y','-ss',str(START),'-t',str(SOURCE_DURATION),'-i',str(SOURCE),
                        '-map','[v]','-an','-filter_complex',filters,
                        '-c:v','libx264','-preset','slow','-crf',str(crf),'-maxrate',rate,'-bufsize',str(int(rate[:-1])*2)+'k','-movflags','+faststart',str(target)],check=True)
        subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(target),'-f','null','-'],check=True)
        metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(target)]))
        video=next(s for s in metadata['streams'] if s['codec_type']=='video')
        assert abs(float(metadata['format']['duration'])-DURATION)<.05
        assert not any(s['codec_type']=='audio' for s in metadata['streams'])
        outputs[name]=dict(width=video['width'],height=video['height'],fps=fps,bytes=target.stat().st_size,loop_check=verify_loop(target))
        print(name,outputs[name],flush=True)
    frame=ROOT/'_media_work/mrasi-film-poster.png'
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(START),'-i',str(SOURCE),'-map','0:v:0','-an','-frames:v','1','-vf','scale=1600:-2',str(frame)],check=True)
    with Image.open(frame) as im:
        im.save(OUT/'mrasi-alsaada-2-loop-poster.webp','WEBP',quality=87,method=6)
        im.resize((800,450),Image.Resampling.LANCZOS).save(OUT/'mrasi-alsaada-2-loop-poster-mobile.webp','WEBP',quality=84,method=6)
    video=dict(source_id=IDENT,source_path='Client/01-Architecture & Interiors/Buildings/02-MARRASI 2/night view 2.mp4',
               start_seconds=START,source_duration_seconds=SOURCE_DURATION,playback_speed=1,duration_seconds=round(DURATION,6),
               label='Mrasi Al Saada 2 · Film',alt='Animated architectural visualization of Mrasi Al Saada 2 supplied by Meridian',
               loop_treatment='Forward/reverse loop with duplicate endpoint frames removed',
               desktop_fps=24,mobile_fps=24,source_width=3840,source_height=2160,poster_width=1600,poster_height=900,outputs=outputs,
               desktop='assets/media/mrasi-alsaada-2-loop-desktop.mp4',mobile='assets/media/mrasi-alsaada-2-loop-mobile.mp4',
               poster='assets/media/mrasi-alsaada-2-loop-poster.webp',poster_mobile='assets/media/mrasi-alsaada-2-loop-poster-mobile.webp',
               note='Source 0.5–8.5s forward, then reversed at native 24fps. Both duplicated endpoint frames removed for continuous forward/reverse playback. Silent; complete decode and adjacent-frame seam checks passed.')
    for filename in ('tools/media_selections.json','assets/media/catalog.json'):
        path=ROOT/filename
        catalog=json.loads(path.read_text(encoding='utf8'));catalog['video']=video
        path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':main()
