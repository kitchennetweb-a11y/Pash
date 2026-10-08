# Robo clip -> Pash voice: trim silence, light robot effect, compress, level-match, mp3
import subprocess, numpy as np, os, sys, tempfile
SR = 44100
SRC = '/mnt/user-data/uploads/audio/'
OUT = '/home/claude/voice/'
MAP = dict(
    ab='w_water', ab_mikham='want_water', ab_khonak='x_ab_khonak',
    cheshm='w_eye', goosh='w_ear', dahan='w_mouth', nan='w_bread', shir='w_milk', shekamam='this_belly',
    cheragh='w_lamp', cheragh_roshan='x_cheragh_roshan', cheragh_khamoosh='x_cheragh_khamoosh',
    ketab='w_book', takht='w_bed', in_takhte_mane='x_in_takhte_mane', miz='w_table', sandali='w_chair', bekhab='x_bekhab',
)
MAP.update(toop='w_ball',sib='w_apple',moz='w_banana',khers='w_teddy',mashin='w_car',sar='w_head',dast='w_hand',shekam='w_belly',pa='w_feet',
  sib_mikham='want_apple',moz_mikham='want_banana',nan_mikham='want_bread',shir_mikham='want_milk',in_sarame='this_head',in_dastame='this_hand',bia_bazi='play')
for k in ['akh_saram','oops','ghelghelakam_miad','hahaha','pam_ro_zadi','sib_khoshmaze','moz_dooset_daram','shir_khordam','afarin_kheili_khoob','bache_khoob',
          'sobh_bekheir','khabam_miad','oftadam','hapche','dobare','salam_doostam','in_chi_bood','gorosnam','dooset_daram','vay','ser_shodam']:
    MAP[k]='x_'+k
for k in ['bepar','bepar_bala','becharkh','dast_bezan','beshin','beraghs','biya_beraghsim','bala','paein','miram_bala','miam_paein',
          'dobare_dobare','mamnoon','salam','shab_bekheir','akh','oh','sar_gij','ghelghelaki','boo_mide','bidar_shodam','pashodam',
          'yavash','yavash_tar','begir','man_bozorgam','bozorg','koochak']:
    MAP[k] = 'x_' + k

def run(args, inp=None):
    return subprocess.run(args, input=inp, capture_output=True).stdout

def load(p, af=None):
    a = ['ffmpeg', '-loglevel', 'error', '-i', p]
    if af: a += ['-af', af]
    return np.frombuffer(run(a + ['-ac', '1', '-ar', str(SR), '-f', 'f64le', '-']), np.float64).copy()

def lufs(p):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', p, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(r.split('Integrated loudness:')[1].split('I:')[1].split('LUFS')[0])

def robot(x):  # no effect: clean voice, just normalised
    return x / (np.max(np.abs(x)) + 1e-9) * 0.5

TARGET = -9.0
names = sys.argv[1:] or list(MAP)
for name in names:
    key = MAP[name]
    x = load(SRC + name + '.mp3', 'silenceremove=start_periods=1:start_threshold=-50dB,afade=t=in:d=0.01')
    y = robot(x)
    with tempfile.TemporaryDirectory() as td:
        a, c = td + '/a.wav', td + '/c.wav'
        run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'f64le', '-ar', str(SR), '-ac', '1', '-i', '-', '-af',
             'acompressor=threshold=0.06:ratio=5:attack=3:release=90:knee=4', '-c:a', 'pcm_s16le', c], y.tobytes())
        g = TARGET - lufs(c)
        run(['ffmpeg', '-loglevel', 'error', '-y', '-i', c, '-af', f'volume={g:.2f}dB,alimiter=limit=0.72:attack=1:release=40:level=disabled,apad=pad_dur=0.35',
             '-ac', '1', '-b:a', '64k', OUT + key + '.mp3'])
    print(key, end=' ')
print()
