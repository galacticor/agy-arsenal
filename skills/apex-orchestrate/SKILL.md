---
name: apex-orchestrate
description: >-
  License-compliant, in-app multi-agent orchestrator (`/apex-orchestrate`).
  Runs a structured 5-phase Plan -> Wave Dispatch -> Scope-Firewalled Merge-Back
  -> Deterministic Gate -> Heterogeneous Verifier loop using native subagents
  and `orch_ctl.py`.
---

# `/apex-orchestrate` — In-App Multi-Agent Orchestrator

Use `/apex-orchestrate` **only for T3 tasks (`F >= 4` touched files AND `M >= 2` strictly disjoint modules)** when built-in `Orchestrator` / `/swarm` / `/run-workflow` are unavailable or when you want a deterministic **Plan → Execute → Merge-Back → Gate → Verify** pipeline inside Antigravity. For complex T3 tasks (`R == 1` or cross-module interface coupling), consult **`/agentspace-advisor` (Carbon)** upfront to lock shared interfaces and disjoint `owned_files` before dispatching worktrees. For `1–3` file serial tasks, use `/apex-exec` (on Medium) or `/apex-architect` (on Low); reserve `/agentspace-advisor` on serial tasks for hard problem-solving (`R == 1` or 2-strike failure).

---

## Phase 1 — Pre-Flight, Schema Lock & Verbatim-Contract Decomposition
1. Initialize the run state:
   ```bash
   python3 ~/.gemini/config/skills/apex-orchestrate/scripts/orch_ctl.py init --run-id <slug> --spec-text "<goal>"
   ```
2. **Turn-0 Subagent Registration (Before Research/Reads)**: Read `~/.gemini/config/skills/apex-orchestrate/references/subagent-contracts.md` and call `define_subagent` for `apex-implementer` and `apex-verifier` **before** launching `research` subagents or reading repo files so tool-schema updates never invalidate cached Coordinator context.
3. **Locator Scout + Interface Lock**: For unfamiliar large codebases, fan out read-only `research` subagents returning **exact `path:line` contracts, verbatim interface signatures, and invariant constraints** (never vague prose summaries). For `R == 1` or coupled interfaces, lock shared types/SQL invariants in `.apex-orch/<slug>/spec.md` (via Carbon or `/boost` upfront) before dispatching workers.
4. Choose workspace topology:
   - **Single worker or sequential chain:** `Workspace: "inherit"` (zero merge overhead, works on dirty trees and non-Git folders).
   - **2 to 4 independent tasks with strictly disjoint `owned_files`:** `Workspace: "share"` (cap concurrency at **4 workers** per wave).

---

## Phase 2 — Time-Boxed Wave Dispatch & `<210s` Watchdog
1. Invoke `apex-implementer` (`Model: "flash"`, prompt prefixed with `[EFFORT: HIGH]` or `[EFFORT: MEDIUM]`; **never** `flash_lite`). Scope each worker's in-worktree check to **compile + module-local & contract unit tests (`<= 180s`)**; defer slow repo-wide suites to Phase 3 so workers finish inside the cache window.
2. Arm a single `schedule` watchdog timer (`TimerCondition: "any"`, **`210s`** — never `>= 300s`, preserving a `90s` buffer before parent KV-cache expiry) when launching parallel background waves, then end your turn and wait for reactive wakeup (do **not** poll). Cap idle watchdog wakeups without worker progress at **2 cycles (`420s`)** before inspecting worker status.
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

## Phase 3 — Mandatory Full-Suite Deterministic Gate (Outer Regression Shield)
1. Because Phase 2 waves run fast `<180s` targeted checks, Phase 3 MUST run the **complete cross-module test, lint, typecheck, and data-invariant suite** on the integrated parent checkout:
   ```bash
   python3 ~/.gemini/config/skills/apex-orchestrate/scripts/orch_ctl.py gate --run-id <slug> -- <command...>
   ```
   *(Never skip Phase 3 even when all Phase 2 module tests pass; never run unscoped `git diff` directly into Coordinator stdout.)*
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
