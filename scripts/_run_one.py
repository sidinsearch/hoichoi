import json, subprocess, time, urllib.request

API = "http://127.0.0.1:8000"


def post(path, payload):
    """This endpoint takes multipart form fields, not a JSON body."""
    boundary = "----hoichoi-boundary"
    parts = []
    for k, v in payload.items():
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'
        )
    body = ("".join(parts) + f"--{boundary}--\r\n").encode()
    req = urllib.request.Request(
        API + path, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print("error detail:", e.read().decode()[:800], flush=True)
        raise SystemExit(1)


def get(path):
    with urllib.request.urlopen(API + path, timeout=30) as r:
        return json.loads(r.read().decode())


job = post("/api/analyze-resource", {
    "resource_name": "mohanagar.mp4",
    "brand_name": "brands.json",
    "language": "bn",
})
jid = job.get("job_id") or job.get("id")
print("job:", jid, flush=True)

for i in range(120):
    time.sleep(8)
    try:
        s = get(f"/api/jobs/{jid}")
    except Exception as exc:
        print("poll err", exc, flush=True)
        continue
    print(f"[{i}] {s.get('status')} {s.get('progress')} {s.get('stage','')}", flush=True)
    if s.get("status") in {"completed", "failed", "error"}:
        break

print("FINAL_JOB=" + str(jid), flush=True)
print("SUMMARY=" + json.dumps(get(f"/api/jobs/{jid}").get("summary")), flush=True)
