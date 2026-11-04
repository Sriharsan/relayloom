"""Write the Kaggle notebook that runs Muse Glimmer 30B and SAM 3.1 on a free Kaggle GPU and saves real timings.

Usage: python scripts/make_kaggle_notebook.py   ->  kaggle/relayloom-gpu.ipynb
Import that file in Kaggle (New Notebook, File, Import Notebook), choose the GPU T4 x2 accelerator, turn Internet on, and add
your Hugging Face read token as a Kaggle secret named HF_TOKEN. Run all. Results land in /kaggle/working/gpu/.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CELLS = [
    ("markdown", "# Relayloom on a Kaggle GPU\nMuse Glimmer 30B Q4_K_M (llama.cpp, CUDA) and SAM 3.1 (Ultralytics) over the repository's bills and photos. Real timings are saved to `/kaggle/working/gpu/`."),
    ("code", "!nvidia-smi --query-gpu=name,memory.total --format=csv\n!nproc && free -g | head -2"),
    ("code", "!pip -q install ultralytics huggingface_hub segno cryptography PyMuPDF\n"
             "!rm -rf relayloom && git clone -q https://github.com/Sriharsan/relayloom.git && cd relayloom && git log --format='%h %an %s' -1"),
    ("code", "# Build llama.cpp with CUDA for the Kaggle T4 (architecture 75). About ten minutes, once.\n"
             "!git clone -q --depth 1 https://github.com/ggml-org/llama.cpp.git\n"
             "!cd llama.cpp && cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=75 -DCUDAToolkit_ROOT=/usr/local/cuda -DCMAKE_LIBRARY_PATH=/usr/local/cuda/lib64/stubs -DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release 2>&1 | tail -5 && cmake --build build --target llama-server -j 4 2>&1 | tail -3"),
    ("code", "import os\n"
             "from kaggle_secrets import UserSecretsClient\n"
             "os.environ['HF_TOKEN'] = UserSecretsClient().get_secret('HF_TOKEN')  # your own token, from Kaggle secrets; never printed\n"
             "from huggingface_hub import hf_hub_download\n"
             "os.makedirs('/kaggle/temp/models', exist_ok=True)\n"
             "hf_hub_download('facebook/sam3.1', 'sam3.1_multiplex.pt', local_dir='/kaggle/temp/models', token=os.environ['HF_TOKEN'])\n"
             "for name in ('Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf', 'mmproj-Muse-Glimmer-30B-Q4_K_M.gguf'):\n"
             "    hf_hub_download('meta-models/Muse-Glimmer-30B-GGUF', name, local_dir='/kaggle/temp/models', token=os.environ['HF_TOKEN'])\n"
             "print(sorted(os.listdir('/kaggle/temp/models')))"),
    ("code", "import subprocess, time, urllib.request\n"
             "server = subprocess.Popen(['/kaggle/working/llama.cpp/build/bin/llama-server', '-m', '/kaggle/temp/models/Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf',\n"
             "    '--mmproj', '/kaggle/temp/models/mmproj-Muse-Glimmer-30B-Q4_K_M.gguf', '--host', '127.0.0.1', '--port', '8084', '--jinja', '-c', '8192', '-np', '1',\n"
             "    '-ngl', '99', '--split-mode', 'layer', '--reasoning-budget', '1024', '--chat-template-kwargs', '{\"reasoning_strength\":\"low\"}'],\n"
             "    stdout=open('/kaggle/working/llama.log', 'w'), stderr=subprocess.STDOUT)\n"
             "for _ in range(180):\n"
             "    try:\n"
             "        if urllib.request.urlopen('http://127.0.0.1:8084/health', timeout=3).status == 200: break\n"
             "    except Exception: time.sleep(5)\n"
             "print('Glimmer is up on both GPUs')"),
    ("code", "import json, sys, time\n"
             "os.chdir('/kaggle/working/relayloom'); sys.path.insert(0, '.')\n"
             "os.environ['RELAYLOOM_MODELS'] = '/kaggle/temp/models'\n"
             "from relayloom.ap.models import GlimmerClient, SamCounter\n"
             "from relayloom.ap.lookagent import LookAgent\n"
             "ROUTE = 'Muse Glimmer 30B Q4_K_M and SAM 3.1, Kaggle GPU T4 x2'\n"
             "glimmer = GlimmerClient('http://127.0.0.1:8084/v1', ROUTE, timeout=900)\n"
             "sam = SamCounter(sys.executable, '/kaggle/temp/models/sam3.1_multiplex.pt', ROUTE, live=True, cache=__import__('pathlib').Path('/kaggle/working/gpu/sam'))\n"
             "os.makedirs('/kaggle/working/gpu', exist_ok=True)\n"
             "# 1. Glimmer reads one bill, timed\n"
             "from relayloom.ap.masking import mask\n"
             "text = open('fixtures/bills/ARD-5101.txt', encoding='utf-8').read()\n"
             "read = glimmer.read_bill(mask(text)[0])\n"
             "print('bill read in', read['seconds'], 's, total', read['bill']['total_inr'])\n"
             "bill_seconds = read['seconds']"),
    ("code", "# 2. The agent loop on every photo that has a known answer: first try vs after the loop\n"
             "import pathlib\n"
             "photos = json.load(open('fixtures/data.json'))\n"
             "truth = {p['id']: p for e in photos['receiving_events'] for p in e['photos']}\n"
             "agent = LookAgent(glimmer, sam)\n"
             "rows = []\n"
             "for pid in sorted(truth)[:12]:\n"
             "    path = pathlib.Path('fixtures/photos') / truth[pid]['file']\n"
             "    event = next(e for e in photos['receiving_events'] if any(p['id'] == pid for p in e['photos']))\n"
             "    item = photos['items'][event['item_code']]\n"
             "    found = agent.look(path, item['name'], pid)\n"
             "    rows.append({'photo': pid, 'agreed': found['agreed'], 'count': found['count'], 'first_try': found['first_try_count'], 'calls': found['calls'], 'seconds': found['seconds']})\n"
             "    print(rows[-1])\n"
             "json.dump({'route': ROUTE, 'bill_read_seconds': bill_seconds, 'rows': rows}, open('/kaggle/working/gpu/agent-loop.json', 'w'), indent=1)"),
]


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
