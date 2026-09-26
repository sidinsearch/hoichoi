"""Is a local VLM viable at all on 1 aarch64 core? Measure the cost breakdown."""
import time, torch
from pathlib import Path
from PIL import Image

torch.set_num_threads(1)
from transformers import AutoProcessor, AutoModelForImageTextToText

M = "HuggingFaceTB/SmolVLM-256M-Instruct"
proc = AutoProcessor.from_pretrained(M)
model = AutoModelForImageTextToText.from_pretrained(M, dtype=torch.float32).eval()

frame = sorted(Path("data/jobs/job_1790431526971/frames").glob("*.jpg"))[0]
msg = [{"role": "user", "content": [
    {"type": "image"},
    {"type": "text", "text": "Describe the setting in one short sentence."}]}]
prompt = proc.apply_chat_template(msg, add_generation_prompt=True)

# Cost of image encoding alone (no autoregressive decode).
im = Image.open(frame).convert("RGB")
for size in (256, 384, 512):
    ims = im.copy(); ims.thumbnail((size, size))
    inp = proc(text=prompt, images=[ims], return_tensors="pt")
    t = time.time()
    with torch.no_grad():
        out = model.generate(**inp, max_new_tokens=1, do_sample=False)
    print(f"encode-only @{size}px: {time.time()-t:.1f}s", flush=True)

# Full run, small image, short output.
for size in (256, 384):
    ims = im.copy(); ims.thumbnail((size, size))
    inp = proc(text=prompt, images=[ims], return_tensors="pt")
    t = time.time()
    with torch.no_grad():
        out = model.generate(**inp, max_new_tokens=20, do_sample=False)
    dt = time.time() - t
    txt = proc.batch_decode(out, skip_special_tokens=True)[0].split("Assistant:")[-1].strip()
    print(f"full @{size}px 20tok: {dt:.1f}s :: {txt[:80]}", flush=True)

# What does the deterministic pixel path cost, same frame?
from app.backend.services import vlm
t = time.time()
for _ in range(20):
    vlm._analyze_frame_cheap(frame)
print(f"pixel analysis x20: {time.time()-t:.2f}s "
      f"({(time.time()-t)/20*1000:.0f}ms/frame)", flush=True)
print("BENCH2_DONE", flush=True)
