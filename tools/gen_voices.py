# Generate Pash voice clips with ElevenLabs. Resumable: skips files that already exist.
# Usage: python gen_voices.py VOICE_ID MODEL_ID [--budget=N] [file_name ...]   (no file names = all rows)
# --budget: stop before N characters; character lines first, then whole words (all 4 lines) in list order
# API key comes from ELEVENLABS_API_KEY (process env, or the Windows user env set with setx). Never printed.
import csv, json, os, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
CSVS = [os.path.join(HERE, '..', 'vocab', f) for f in ('lines_existing_v2.csv', 'lines_words_v2.csv', 'lines_games_v2.csv', 'lines_night_v2.csv')]
OUT = r'C:\Users\ahmma\Downloads\Virtual Pet Sounds\v2'
SKIP = {'name.mp3'}  # personal greeting, keep the original

def api_key():
    k = os.environ.get('ELEVENLABS_API_KEY')
    if not k and os.name == 'nt':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment') as h:
                k = winreg.QueryValueEx(h, 'ELEVENLABS_API_KEY')[0]
        except OSError:
            pass
    if not k:
        sys.exit('ELEVENLABS_API_KEY is not set')
    return k

KEY = api_key()

def req(url, body=None):
    r = urllib.request.Request(url, data=body and json.dumps(body).encode(),
                               headers={'xi-api-key': KEY, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(r, timeout=90) as f:
        return f.read()

def quota():
    s = json.loads(req('https://api.elevenlabs.io/v1/user/subscription'))
    return s['character_limit'] - s['character_count']

def gen(row, voice, model):
    path = os.path.join(OUT, row['file_name'])
    if os.path.exists(path):
        return None
    url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128'
    for attempt in range(6):
        try:
            data = req(url, {'text': row['farsi_text'], 'model_id': model})
            if len(data) < 2048 or data[:3] not in (b'ID3', b'\xff\xfb', b'\xff\xf3', b'\xff\xf2'):
                raise ValueError('not a valid mp3')
            with open(path, 'wb') as f:
                f.write(data)
            return None
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                return f'{row["file_name"]}: HTTP {e.code} {e.read()[:200]!r}'
            err = f'HTTP {e.code}'
            time.sleep(10 if e.code == 429 else 2 * (attempt + 1))
        except Exception as e:
            err = str(e)
            time.sleep(2 * (attempt + 1))
    return f'{row["file_name"]}: {err}'

if __name__ == '__main__':
    args = [a for a in sys.argv[3:] if not a.startswith('--budget=')]
    budget = int(next((a[9:] for a in sys.argv[3:] if a.startswith('--budget=')), 10**9))
    voice, model, only = sys.argv[1], sys.argv[2], set(args)
    os.makedirs(OUT, exist_ok=True)
    rows = [r for f in CSVS if os.path.exists(f) for r in csv.DictReader(open(f, encoding='utf-8-sig'))
            if r['file_name'] not in SKIP and (not only or r['file_name'] in only)]
    todo = [r for r in rows if not os.path.exists(os.path.join(OUT, r['file_name']))]
    # cut at the budget, keeping each word's lines together (w_/say_/where_/this_ share the id)
    word = lambda r: 'word:' + r['file_name'].split('_', 1)[1] if r['file_name'][:2] in ('w_', 'sa', 'wh', 'th') and '_' in r['file_name'] else r['file_name']
    keep, used, cut = [], 0, set()
    for r in todo:
        if word(r) in cut or used + len(r['farsi_text']) > budget:
            cut.add(word(r)); continue
        keep.append(r); used += len(r['farsi_text'])
    keep = [r for r in keep if word(r) not in cut]
    if cut:
        print(f'Over budget, left for later: {len(todo) - len(keep)} clips')
    todo = keep
    need = sum(len(r['farsi_text']) for r in todo)
    left = quota()
    print(f'{len(todo)} clips to make, ~{need} characters, {left} characters left on your plan')
    if need > left:
        sys.exit('Not enough characters left, stopping.')
    with ThreadPoolExecutor(3) as ex:
        fails = [f for f in ex.map(lambda r: gen(r, voice, model), todo) if f]
    print(f'Done: {len(todo) - len(fails)} made, {len(fails)} failed, ~{need} characters used')
    for f in fails:
        print('  FAILED', f)
