# Results from our own runs

Every number on this page comes from a run on the machine below, on synthetic records.
Recorded outputs are in `fixtures/recorded/`, each with its date, route, model and timings.

## The machine (checked 31 October 2026)

| Part | Value |
| --- | --- |
| Operating system | Windows 11 Home, version 10.0.26300 |
| CPU | Intel Core Ultra 7 155U, 12 cores, 14 threads |
| Memory | 31.4 GB (about 4 GB free while Docker, ERPNext and the usual desktop apps ran) |
| GPU | Intel integrated graphics, no NVIDIA GPU, so no `nvidia-smi` |
| Free disk | C: 43.9 GB, D: 399.5 GB |
| Ollama | 0.17.1 installed (not used: it predates Muse Glimmer support) |
| Docker | Docker Desktop, engine 28.1.1, running |
| Tesseract | Not installed. Masking works on the text layer of PDF bills only. |

Route chosen for Muse Glimmer: **4.3b, CPU on this laptop**. There is no GPU with 24 GB.
llama.cpp release b12020 (Windows CPU build), file
`Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf` from `meta-models/Muse-Glimmer-30B-GGUF`
(Apache 2.0, 16,756,683,904 bytes), served by `llama-server --jinja -c 8192 -np 1 -t 10
--no-repack --reasoning-budget 1024` with `reasoning_strength` low. Weight repacking was
turned off because it needs 12 GB of extra committed memory that this machine did not have
free. Loading took 51 seconds.

## Muse Glimmer reading bills (real, on this laptop)

Text layer of each synthetic PDF bill, masked first, then read into the strict schema.
"Valid" means the output passed `validate_bill` and equals the bill's true values.

| Bill | Seconds | Prompt tokens | Output tokens | Prompt speed | Output speed | Result |
| --- | --- | --- | --- | --- | --- | --- |
| VEL-2611 | 491.0 | 362 | 404 | 3.5 tokens/s | 1.04 tokens/s | valid |
| PON-0457 | 446.9 | 366 | 387 |  |  | valid |

Slow but real: about 7 to 8 minutes a bill on a laptop CPU with little free memory. Bills
run as a background batch. The Today screen shows these timings, never faster ones.

## SAM 3.1 counting delivered goods

Waiting on access to the gated `facebook/sam3.1` weights (see the checkpoint). Not run yet.
