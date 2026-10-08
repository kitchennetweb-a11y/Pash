# Raw ElevenLabs clips -> Pash clips: pitch +2 st, trim leading silence, light compression, loudness-match, 0.35 s tail.
# Usage: python tools/process_robo_clips.py [SRC_DIR] [OUT_DIR] [file_name ...]
import glob, os, shutil, subprocess, sys, tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\ahmma\Downloads\Virtual Pet Sounds\v2'
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'audio')
ONLY = set(sys.argv[3:])
TARGET = -9.0  # LUFS, same as the first set
PITCH = 2 ** (2 / 12)  # +2 semitones, formants shifted too ("up2 cute", chosen 2026-10-08)
FF = shutil.which('ffmpeg') or next(iter(glob.glob(os.path.expandvars(
    r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe'))), 'ffmpeg')

def ff(*a):
    return subprocess.run([FF, '-hide_banner', '-loglevel', 'info', '-y', *a], capture_output=True, text=True, encoding='utf-8', errors='replace')

def lufs(p):
    e = ff('-i', p, '-af', 'ebur128', '-f', 'null', '-').stderr
    return float(e.rsplit('I:', 1)[1].split('LUFS')[0])

files = sorted(glob.glob(os.path.join(SRC, '*.mp3')))
os.makedirs(OUT, exist_ok=True)
with tempfile.TemporaryDirectory() as td:
    c = os.path.join(td, 'c.wav')
    for f in files:
        name = os.path.basename(f)
        if ONLY and name not in ONLY:
            continue
        # trim only the leading silence (natural ending kept), tiny fade-in so the cut doesn't click, light compression
        ff('-i', f, '-ac', '1', '-ar', '44100', '-af',
           f'rubberband=pitch={PITCH},silenceremove=start_periods=1:start_threshold=-50dB,afade=t=in:d=0.01,'
           'acompressor=threshold=0.06:ratio=3:attack=5:release=90:knee=4', c)
        g = TARGET - lufs(c)
        ff('-i', c, '-af', f'volume={g:.2f}dB,alimiter=limit=0.72:attack=1:release=40:level=disabled,apad=pad_dur=0.35',
           '-ac', '1', '-b:a', '64k', os.path.join(OUT, name))
        print(name, f'{g:+.1f} dB')
