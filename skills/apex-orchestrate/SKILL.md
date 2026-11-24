---
name: apex-orchestrate
description: >-
  License-compliant, in-app multi-agent orchestrator (`/apex-orchestrate`).
  Runs a structured 5-phase Plan -> Wave Dispatch -> Scope-Firewalled Merge-Back
  -> Deterministic Gate -> Heterogeneous Verifier loop using native subagents
  and `orch_ctl.py`.
---

# `/apex-orchestrate` — In-App Multi-Agent Orchestrator

Use `/apex-orchestrate` for large, multi-file, or parallelizable tasks when built-in `Orchestrator` / `/swarm` / `/run-workflow` are unavailable or when you want a deterministic **Plan → Execute → Merge-Back → Gate → Verify** pipeline inside Antigravity.

---

## Phase 1 — Pre-Flight, Research & Decomposition
1. Initialize the run state:
   ```bash
   python3 ~/.gemini/config/skills/apex-orchestrate/scripts/orch_ctl.py init --run-id <slug> --spec-text "<goal>"
   ```
2. For unfamiliar large codebases, fan out built-in read-only `research` subagents first so raw file reads never bloat Coordinator context.
3. Read `~/.gemini/config/skills/apex-orchestrate/references/subagent-contracts.md` and call `define_subagent` for `apex-implementer` and `apex-verifier` if not yet registered in this conversation.
4. Choose workspace topology:
   - **Single worker or sequential chain:** `Workspace: "inherit"` (zero merge overhead, works on dirty trees and non-Git folders).
   - **2 to 4 independent tasks with strictly disjoint `owned_files`:** `Workspace: "share"` (cap concurrency at **4 workers** per wave).

---

## Phase 2 — Wave Dispatch & Watchdog
1. Invoke `apex-implementer` (`Model: "flash"`, prompt prefixed with `[EFFORT: HIGH]` or `[EFFORT: MEDIUM]`; **never** `flash_lite`).
2. Arm a single `schedule` watchdog timer (`TimerCondition: "any"`, 300s) when launching parallel background waves, then end your turn and wait for reactive wakeup (do **not** poll).
3. **Critical Lifecycle Rule:** Do **NOT** call `manage_subagents(Action="kill")` on any `Workspace: "share"` subagent until Phase 2.5 cherry-pick succeeds—killing a subagent immediately destroys its temporary worktree.

---

## Phase 2.5 — Scope Firewall & Merge-Back (For `Workspace: "share"`)
1. If a `share` worker reports a pre-merge failure or forgot to commit, wake that same `conversationId` via `send_message` (max 1 retry) so it repairs inside its worktree.
2. For each completed `share` worker, integrate its commit:
   ```bash
   python3 ~/.gemini/config/skills/apex-orchestrate/scripts/orch_ctl.py integrate --run-id <slug> --task-id <id> --ref <head_sha> --owned <csv>
   ```
3. On conflict or scope violation, reject the commit and re-execute that task sequentially using `Workspace: "inherit"`.

---

## Phase 3 — Context-Firewalled Deterministic Gate
1. Run each test/lint/typecheck command on the integrated parent checkout:
   ```bash
   python3 ~/.gemini/config/skills/apex-orchestrate/scripts/orch_ctl.py gate --run-id <slug> -- <command...>
   ```
   *(Never run unscoped `git diff` directly into Coordinator stdout.)*
2. **Post-Merge Repair Routing:** If any gate fails, do **not** `send_message` stale `Workspace: "share"` workers. Invoke a single sequential `apex-implementer` (`Workspace: "inherit"`, `Model: "flash"`, `[EFFORT: HIGH]`) pointing at `.apex-orch/<run_id>/gate.log`. Cap at **2 repair rounds**; if still failing, escalate to `/agentspace-advisor` or offer `orch_ctl.py cleanup --run-id <slug> --rollback`.

---

## Phase 4 — Heterogeneous Verification & Teardown
1. Invoke `apex-verifier` with `Model: "pro"` (if unavailable, retry with `Model: "inherit"` + `[EFFORT: HIGH]`), passing `.apex-orch/<run_id>/{spec.md,combined.diff,gate.log}`.
2. If `VERDICT: NEEDS_CHANGES`, route blockers through one `Workspace: "inherit"` implementer and re-run Phase 3 before re-verifying (max 1 verifier repair cycle).
3. **Mandatory Cleanup:** Call `manage_subagents(Action="kill_all")` and run:
   ```bash
   python3 ~/.gemini/config/skills/apex-orchestrate/scripts/orch_ctl.py cleanup --run-id <slug>
   ```
   so `Stop` hooks observe a clean, verified workspace before presenting the final summary.
