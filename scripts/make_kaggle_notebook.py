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
!rm -rf relayloom && git clone -q https://github.com/Sriharsan/relayloom.git && cd relayloom && git log --format='%h %an %s' -1"""

LLAMA = """# llama.cpp prebuilt for Ubuntu with CUDA 12.8 (release b12098), so nothing is compiled
TAG = 'b12098'
BASE = f'https://github.com/ggml-org/llama.cpp/releases/download/{TAG}/'
!mkdir -p /kaggle/working/llama && cd /kaggle/working/llama && wget -q {BASE}llama-{TAG}-bin-ubuntu-cuda-12.8-x64.tar.gz {BASE}cudart-llama-{TAG}-bin-ubuntu-cuda-12.8-x64.tar.gz && for f in *.tar.gz; do tar xzf $f; done
!find /kaggle/working/llama -name llama-server | head -2"""

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
os.environ['LD_LIBRARY_PATH'] = os.path.dirname(binary) + ':' + os.environ.get('LD_LIBRARY_PATH', '')
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
print(open('/kaggle/working/llama.log').read()[-900:])"""

SETUP = """import json, sys, time, pathlib
os.chdir('/kaggle/working/relayloom'); sys.path.insert(0, '.')
from relayloom.ap.models import GlimmerClient, SamCounter
from relayloom.ap.lookagent import LookAgent
ROUTE = 'Muse Glimmer 30B Q4_K_M and SAM 3.1, Kaggle GPU T4 x2'
glimmer = GlimmerClient('http://127.0.0.1:8084/v1', ROUTE, timeout=900)
sam = SamCounter(sys.executable, '/kaggle/temp/models/sam3.1_multiplex.pt', ROUTE, live=True, cache=pathlib.Path('/kaggle/working/gpu/sam'))
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
    path = pathlib.Path('fixtures/photos') / truth[pid]['file']
    event = next(e for e in photos['receiving_events'] if any(p['id'] == pid for p in e['photos']))
    item = photos['items'][event['item_code']]
    found = agent.look(path, item['name'], pid)
    rows.append({'photo': pid, 'agreed': found['agreed'], 'count': found['count'], 'first_try': found['first_try_count'], 'calls': found['calls'], 'seconds': found['seconds'], 'trace': found['trace']})
    print({k: v for k, v in rows[-1].items() if k != 'trace'})
json.dump({'route': ROUTE, 'bill_read_seconds': bill_seconds, 'rows': rows}, open('/kaggle/working/gpu/agent-loop.json', 'w'), indent=1)"""

CELLS = [("markdown", INTRO), ("code", GPU), ("code", INSTALL), ("code", LLAMA), ("code", MODELS), ("code", SERVER), ("code", SETUP), ("code", LOOP)]


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
