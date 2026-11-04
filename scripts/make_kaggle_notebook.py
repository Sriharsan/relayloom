"""Write the Kaggle notebook that runs Muse Glimmer 30B and SAM 3.1 on a free Kaggle GPU and saves real timings.

Usage: python scripts/make_kaggle_notebook.py   ->  kaggle/relayloom-gpu.ipynb
Import that file in Kaggle (New Notebook, File, Import Notebook), choose the GPU T4 x2 accelerator, turn Internet on, and add
your Hugging Face read token as a Kaggle secret named HF_TOKEN. Run all. Results land in /kaggle/working/gpu/.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INTRO = """# Relayloom on a Kaggle GPU
Muse Glimmer 30B Q4_K_M (llama.cpp, CUDA) and SAM 3.1 (Ultralytics) over the repository's bills and photos. Real timings are saved to `/kaggle/working/gpu/`."""

GPU = """!nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
!nproc && free -g | head -2
!df -h /kaggle/working /kaggle/temp | cat"""

INSTALL = """!pip -q install ultralytics huggingface_hub segno cryptography PyMuPDF
!pip -q install git+https://github.com/ultralytics/CLIP.git
!rm -rf relayloom && git clone -q https://github.com/Sriharsan/relayloom.git && cd relayloom && git log --format='%h %an %s' -1"""

LLAMA = """# llama.cpp prebuilt for Ubuntu with CUDA 12.8 (release b12098), so nothing is compiled
import glob, os, tarfile, urllib.request
TAG = 'b12098'
BASE = f'https://github.com/ggml-org/llama.cpp/releases/download/{TAG}/'
os.makedirs('/kaggle/working/llama', exist_ok=True)
for name in (f'llama-{TAG}-bin-ubuntu-cuda-12.8-x64.tar.gz', f'cudart-llama-{TAG}-bin-ubuntu-cuda-12.8-x64.tar.gz'):
    path = '/kaggle/working/llama/' + name
    urllib.request.urlretrieve(BASE + name, path)
    print(name, os.path.getsize(path), 'bytes')
    tarfile.open(path).extractall('/kaggle/working/llama')
print(glob.glob('/kaggle/working/llama/**/llama-server*', recursive=True)[:5])"""

MODELS = """import os
from kaggle_secrets import UserSecretsClient
os.environ['HF_TOKEN'] = UserSecretsClient().get_secret('HF_TOKEN')  # your own token, from Kaggle secrets; never printed
from huggingface_hub import hf_hub_download
os.makedirs('/kaggle/temp/models', exist_ok=True)
hf_hub_download('facebook/sam3.1', 'sam3.1_multiplex.pt', local_dir='/kaggle/temp/models', token=os.environ['HF_TOKEN'])
for name in ('Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf', 'mmproj-Muse-Glimmer-30B-Q4_K_M.gguf'):
    hf_hub_download('meta-models/Muse-Glimmer-30B-GGUF', name, local_dir='/kaggle/temp/models', token=os.environ['HF_TOKEN'])
print(sorted(os.listdir('/kaggle/temp/models')))"""

SERVER = """import glob, subprocess, time, urllib.request
binary = glob.glob('/kaggle/working/llama/**/llama-server', recursive=True)[0]
libdirs = sorted({os.path.dirname(f) for f in glob.glob('/kaggle/working/llama/**/*.so*', recursive=True)})
os.environ['LD_LIBRARY_PATH'] = ':'.join(libdirs) + ':' + os.environ.get('LD_LIBRARY_PATH', '')
print('library folders:', libdirs)
server = subprocess.Popen([binary, '-m', '/kaggle/temp/models/Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf',
    '--mmproj', '/kaggle/temp/models/mmproj-Muse-Glimmer-30B-Q4_K_M.gguf', '--host', '127.0.0.1', '--port', '8084', '--jinja', '-c', '8192', '-np', '1',
    '-ngl', '99', '--split-mode', 'layer', '--reasoning-budget', '1024', '--chat-template-kwargs', '{"reasoning_strength":"low"}'],
    stdout=open('/kaggle/working/llama.log', 'w'), stderr=subprocess.STDOUT)
started = time.time()
for _ in range(120):
    try:
        if urllib.request.urlopen('http://127.0.0.1:8084/health', timeout=3).status == 200:
            break
    except Exception:
        time.sleep(5)
print('Glimmer up after', round(time.time() - started), 's')
log = open('/kaggle/working/llama.log').read()
print([l for l in log.splitlines() if any(k in l.lower() for k in ('cuda', 'offload', 'gpu', 'device', 'backend'))][:15])
used = sum(int(x) for x in os.popen('nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits').read().split())
print('GPU memory used (MiB):', used)
assert used > 8000, 'Glimmer is not running on the GPU, stopping before any timing is recorded'"""

SETUP = """import json, sys, time, pathlib
print(os.popen('nvidia-smi --query-gpu=memory.used --format=csv').read())
os.chdir('/kaggle/working/relayloom'); sys.path.insert(0, '.')
from relayloom.ap.models import GlimmerClient, SamCounter
from relayloom.ap.lookagent import LookAgent
ROUTE = 'Muse Glimmer 30B Q4_K_M and SAM 3.1, Kaggle GPU T4 x2'
glimmer = GlimmerClient('http://127.0.0.1:8084/v1', ROUTE, timeout=900)
sam = SamCounter(sys.executable, '/kaggle/temp/models/sam3.1_multiplex.pt', ROUTE, live=True, cache=pathlib.Path('/kaggle/working/gpu/sam'), persistent=True)
os.makedirs('/kaggle/working/gpu', exist_ok=True)
from relayloom.ap.masking import mask
text = open('fixtures/bills/ARD-5101.txt', encoding='utf-8').read()
read = glimmer.read_bill(mask(text)[0])
print('bill read in', read['seconds'], 's on the GPU, total', read['bill']['total_inr'])
bill_seconds = read['seconds']"""

LOOP = """photos = json.load(open('fixtures/data.json'))
truth = {p['id']: p for e in photos['receiving_events'] for p in e['photos']}
agent = LookAgent(glimmer, sam)
rows = []
for pid in sorted(truth)[:12]:
    path = pathlib.Path('fixtures') / truth[pid]['file']
    event = next(e for e in photos['receiving_events'] if any(p['id'] == pid for p in e['photos']))
    item = photos['items'][event['item_code']]
    found = agent.look(path, item['name'], pid)
    rows.append({'photo': pid, 'agreed': found['agreed'], 'count': found['count'], 'first_try': found['first_try_count'], 'calls': found['calls'], 'seconds': found['seconds'], 'trace': found['trace']})
    print({k: v for k, v in rows[-1].items() if k != 'trace'})
json.dump({'route': ROUTE, 'bill_read_seconds': bill_seconds, 'rows': rows}, open('/kaggle/working/gpu/agent-loop.json', 'w'), indent=1)"""

TUNING = """# Can Glimmer read the same bill faster? Same bill, same schema, different reasoning settings; every variant is timed and checked against the schema.
from relayloom.ap.schema import BILL_SCHEMA, validate_bill
from relayloom.ap.models import READER_SYSTEM, parse_json
masked = mask(text)[0]
variants = {
    'low (what the product uses)': None,
    'reasoning budget 0': {'reasoning_budget': 0},
    'reasoning strength none': {'chat_template_kwargs': {'reasoning_strength': 'none'}},
    'reasoning strength minimal': {'chat_template_kwargs': {'reasoning_strength': 'minimal'}},
}
tuning = []
for name, extra in variants.items():
    try:
        reply = glimmer.chat(READER_SYSTEM, 'Bill text:' + chr(10) + '<<<' + chr(10) + masked + chr(10) + '>>>', BILL_SCHEMA, extra=extra)
        ok = validate_bill(parse_json(reply['content']))['total_inr'] == read['bill']['total_inr']
        row = {'variant': name, 'seconds': reply['seconds'], 'valid_and_same_total': ok, 'completion_tokens': reply['usage'].get('completion_tokens'),
               'reasoning_chars': reply['reasoning_chars'], 'tokens_per_second': round(reply['timings'].get('predicted_per_second', 0), 1),
               'prompt_tokens_per_second': round(reply['timings'].get('prompt_per_second', 0), 1)}
    except Exception as error:
        row = {'variant': name, 'error': str(error)[:160]}
    tuning.append(row)
    print(row)
json.dump(tuning, open('/kaggle/working/gpu/glimmer-tuning.json', 'w'), indent=1)"""

TRACK = """# Count items as they cross a line in a video: SAM 3.1 follows every item, code counts each id once (relayloom/ap/crossing.py)
import subprocess, glob
from relayloom.ap.crossing import count_crossings
videos = sorted(glob.glob('/kaggle/input/**/*.mp4', recursive=True)) or [str(pathlib.Path('fixtures/video/dock-delivery.mp4').resolve())]
tracking = []
for video in videos[:3]:
    started = time.time()
    done = subprocess.run([sys.executable, '-I', 'relayloom/ap/track_worker.py', '/kaggle/temp/models/sam3.1_multiplex.pt', video, 'cardboard box', '--every', '3'],
                          capture_output=True, text=True, timeout=1500)
    if done.returncode != 0:
        tracking.append({'video': os.path.basename(video), 'error': done.stderr.strip()[-300:]}); print(tracking[-1]); continue
    tracked = json.loads(done.stdout.strip().splitlines()[-1])
    tracks = {k: [tuple(p) for p in v] for k, v in tracked['tracks'].items()}
    best = {}
    for axis in ('x', 'y'):
        found = count_crossings(tracks, 0.5, axis, 'either', margin=0.02)
        best[axis] = found['count']
    row = {'video': os.path.basename(video), 'device': tracked['device'], 'tracked_seconds': tracked['seconds'], 'frames_tracked': tracked['frames'],
           'clip_fps': tracked['fps'], 'tracks_seen': len(tracks), 'crossings_vertical_line': best['x'], 'crossings_horizontal_line': best['y'],
           'wall_seconds': round(time.time() - started, 1)}
    tracking.append(row); print(row)
json.dump(tracking, open('/kaggle/working/gpu/tracking.json', 'w'), indent=1)"""

FINAL = """# Everything in one line each, so the run log carries the result
print('RESULT_AGENT', json.dumps({'route': ROUTE, 'bill_read_seconds': bill_seconds, 'rows': rows}))
print('RESULT_TUNING', json.dumps(tuning))
print('RESULT_TRACKING', json.dumps(tracking))"""

CELLS = [("markdown", INTRO), ("code", GPU), ("code", INSTALL), ("code", LLAMA), ("code", MODELS), ("code", SERVER), ("code", SETUP), ("code", TUNING), ("code", LOOP), ("code", TRACK), ("code", FINAL)]


def main():
    cells = []
    for kind, source in CELLS:
        cell = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True)}
        if kind == "code":
            cell.update({"outputs": [], "execution_count": None})
        cells.append(cell)
    notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                              "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    out = ROOT / "kaggle" / "relayloom-gpu.ipynb"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
