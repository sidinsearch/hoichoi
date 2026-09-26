"""Prove the live key rotation serves real scene context on real frames."""
import os, sys, time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
os.chdir(root)
from dotenv import load_dotenv
load_dotenv()

from app.backend.services import vlm

print("VISION_MODEL:", os.getenv("VISION_MODEL"))
print("gemini keys configured:", len(vlm._api_keys("GEMINI_API_KEY", "GOOGLE_API_KEY")))
print("chain:", vlm._vision_fallbacks("gemini"))

frames = sorted((root / "data/jobs/job_1790431526971/frames").glob("*.jpg"))[:3]
t = time.time()
unknown = 0
for f in frames:
    o = vlm.describe_scene_window([f])
    unknown += o["setting"] == "unknown"
    print(f"  {f.name}: {o['setting']} | acts={o['activities']} | tags={o['context_tags']}")
print(f"\n{len(frames)} windows in {time.time()-t:.1f}s, unknown={unknown}")
print("dead keys:", len(vlm._DEAD_GEMINI_KEYS), "quota-tripped:", sorted(vlm._QUOTA_TRIPPED))
