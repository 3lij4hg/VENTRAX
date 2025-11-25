#!/usr/bin/env python3
"""
Nightly orchestrator audit runner.

Scans the repository workspace for orchestrator/agent files and verifies
whether guard markers are present. Produces a snapshot folder, ZIP archive,
notify summary, and Bridge index entry for traceability.
"""
import json
import os
import re
import zipfile
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Warsaw")
STAMP = datetime.now(TZ).strftime("%Y%m%dT%H%M%S%z")
HUMAN = datetime.now(TZ).strftime("%Y-%m-%d %H:%M %Z")
BASE = "workspace"
OUT = f"{BASE}/ORCH_AUDIT_NIGHTLY_{STAMP}"
os.makedirs(OUT, exist_ok=True)


def sha256(path: str) -> str:
    """Return SHA256 for a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# Scan for orchestrator/agent candidates
scan_ext = {".md", ".yml", ".yaml", ".json", ".txt"}
candidates = []
for root, _, files in os.walk(BASE):
    for fn in files:
        ext = os.path.splitext(fn)[1].lower()
        if ext in scan_ext:
            rp = os.path.join(root, fn)
            rel = os.path.relpath(rp, BASE)
            if any(kw in rel.lower() for kw in ["orch", "orchestrator", "agent"]):
                candidates.append(rp)

guard_markers = re.compile(
    r"(loop[-_ ]?guard|sandboxed_infinity|staged[-_ ]?rollout|checkpoint|snapshot|freeze|hydration)",
    re.I,
)

unguarded, guarded = [], []
for path in candidates:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if guard_markers.search(content):
            guarded.append(path)
        else:
            unguarded.append(path)
    except OSError:
        continue

report = {
    "ts": HUMAN,
    "scanned": len(candidates),
    "guarded": len(guarded),
    "unguarded": len(unguarded),
    "policy": "ORCH-GUARD-ENFORCE active",
}
with open(f"{OUT}/SCAN_REPORT.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
with open(f"{OUT}/GUARDED_LIST.txt", "w", encoding="utf-8") as f:
    f.write("\n".join([os.path.relpath(p, BASE) for p in guarded]))
with open(f"{OUT}/UNGUARDED_LIST.txt", "w", encoding="utf-8") as f:
    f.write("\n".join([os.path.relpath(p, BASE) for p in unguarded]))

# Manifest
paths = []
for root, _, files in os.walk(OUT):
    for fn in files:
        paths.append(os.path.join(root, fn))
with open(f"{OUT}/MANIFEST_SHA256.txt", "w", encoding="utf-8") as f:
    for path in sorted(paths):
        f.write(f"{sha256(path)}  {os.path.relpath(path, BASE)}\n")

# ZIP
zip_path = f"{BASE}/ORCH_AUDIT_NIGHTLY_{STAMP}.zip"
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for path in paths:
        z.write(path, arcname=os.path.relpath(path, BASE))

# Update Bridge
MBI = f"{BASE}/SYSTEM_COVENANTS/MASTER_BRIDGE_INDEX.json"
os.makedirs(os.path.dirname(MBI), exist_ok=True)
if os.path.exists(MBI):
    with open(MBI, "r", encoding="utf-8") as f:
        hub = json.load(f)
else:
    hub = {"generated": HUMAN, "hub": "MASTER_BRIDGE_INDEX.json", "links": []}

hub.setdefault("links", []).append(
    {"name": os.path.basename(zip_path), "path": zip_path, "sha256": sha256(zip_path), "t": HUMAN}
)
with open(MBI, "w", encoding="utf-8") as f:
    json.dump(hub, f, ensure_ascii=False, indent=2)

# Notify file
notify = {
    "when": HUMAN,
    "what": "ORCH-AUDIT nightly",
    "scanned": len(candidates),
    "unguarded": len(unguarded),
    "zip": os.path.basename(zip_path),
    "bridge": MBI,
}
with open(f"{OUT}/NOTIFY.json", "w", encoding="utf-8") as f:
    json.dump(notify, f, ensure_ascii=False, indent=2)

print(json.dumps({"zip": zip_path, "notify": f"{OUT}/NOTIFY.json", "bridge": MBI}, ensure_ascii=False))
