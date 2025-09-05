# VENTRAX
„VENTRAX System Core — nightly audit orchestrators/agents with loop-guards, snapshots &amp; Bridge continuity.”
# Nightly ORCH-AUDIT

**Status:** production • **Schedule:** daily 03:00 Europe/Warsaw (01:00 UTC) • **Last update:** 2025-09-06 00:10 CEST

This workflow scans your repo/workspace for orchestrator/agent files and verifies they are protected by runtime guards
(Loop-Guard, staged rollout, snapshots). It produces a ZIP snapshot, a compact NOTIFY, and a Bridge index for traceability.

---

## What it does

- Scans `workspace/` for files with names containing `orch`, `orchestrator`, or `agent` and extensions: `.md`, `.yml`, `.yaml`, `.json`, `.txt`.
- Detects guard markers in content: `loop-guard`, `sandboxed_infinity`, `staged-rollout`, `checkpoint|snapshot|freeze|hydration`.
- Emits artifacts:\
  - `ORCH_AUDIT_NIGHTLY_{TIMESTAMP}.zip` — full snapshot with report and lists\
  - `ORCH_AUDIT_NIGHTLY_{TIMESTAMP}/NOTIFY.json` — compact mobile-friendly summary\
  - `SYSTEM_COVENANTS/MASTER_BRIDGE_INDEX.json` — append-only index of snapshots\
  - `RUN_LOG.txt` — GH Actions step log
- Returns **`unguarded = 0`** when everything is compliant.

---

## Files created (artifact inventory)

```
workspace/
└─ ORCH_AUDIT_NIGHTLY_{TIMESTAMP}/
   ├─ SCAN_REPORT.json        # scanned, guarded, unguarded counts
   ├─ GUARDED_LIST.txt        # list of guarded files
   ├─ UNGUARDED_LIST.txt      # list of unguarded files (empty when OK)
   ├─ MANIFEST_SHA256.txt     # integrity of files in this folder
   └─ NOTIFY.json             # compact summary
└─ ORCH_AUDIT_NIGHTLY_{TIMESTAMP}.zip
└─ SYSTEM_COVENANTS/
   └─ MASTER_BRIDGE_INDEX.json  # chronological list of snapshot ZIPs
└─ RUN_LOG.txt
```

---

## How to use

1. Ensure `.github/workflows/orch_audit_nightly.yml` is committed (already provided).
2. Push to your repository. Workflow runs nightly at 03:00 Europe/Warsaw or on **Run workflow** (manual).
3. See **Actions → orch-audit-nightly → Summary → Artifacts**.

### Verify integrity

- Open `MANIFEST_SHA256.txt` inside `ORCH_AUDIT_NIGHTLY_{TIMESTAMP}/` and recompute hashes locally:

```bash
sha256sum -c MANIFEST_SHA256.txt
```

- Bridge index (`SYSTEM_COVENANTS/MASTER_BRIDGE_INDEX.json`) should include the new ZIP with its SHA256.

---

## Interpreting results

- **All good:** `unguarded = 0`. `UNGUARDED_LIST.txt` exists but is empty.
- **Action required:** `unguarded > 0`. Patch each file by:
  - including `ORCH_AGENT_GUARD.yml` (policy), or
  - wrapping with the standard wrapper (pre-freeze → staged rollout → post-snapshot → bench → error class).

> Tip: keep an `ORCH_AGENT_WRAPPER_TEMPLATE.md` in your repo for copy-paste.

---

## Troubleshooting

- **Minified React error #185 / Maximum update depth exceeded**\
  This workflow doesn’t render UI, but your orchestrators may cause loops. Make sure your guard policy enables:
  - Loop-Guard with budgets and checkpoints
  - Staged rollout (A→D) for heavy runs
  - PRE/POST snapshots for `/FULL`
  - UI errors classified as `ui_frontend_issue` → notify_only (no core escalation)

- **No files found**\
  The audit looks at names: `orch|orchestrator|agent`. If your naming differs, adjust the regex in `orch_audit_nightly.py`.

- **Time zone / schedule**\
  Cron is set to `01:00 UTC` (= `03:00 Europe/Warsaw`). Adjust `on.schedule.cron` if needed.

---

## Local run (optional)

```bash
python3 workspace/orch_audit_nightly.py
# Artifacts will appear under workspace/ as in CI
```

---

## Security & privacy

- No secrets are requested or stored. \
- Artifacts contain file names and guard markers only; redact sensitive content before committing.

---

## Change log

- 2025-09-06 00:10 CEST: Initial version added (workflow + runner + artifacts schema).

---

## FAQ

**Q: Can it auto-fix unguarded files?**\
A: The workflow only audits. You can extend it to create patch PRs by generating wrapper files and opening a PR via `peter-evans/create-pull-request`.

**Q: Can I scan different folders?**\
A: Edit the base path (`BASE = "workspace"`) and the filename regex in `orch_audit_nightly.py`.

**Q: How do I prove continuity?**\
A: Use `SYSTEM_COVENANTS/MASTER_BRIDGE_INDEX.json` as an append-only ledger: every nightly run appends a new ZIP with its SHA256.
