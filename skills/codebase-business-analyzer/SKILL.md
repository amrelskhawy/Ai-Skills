---
name: codebase-business-analyzer
description: Reverse-engineer a full-stack codebase (frontend, backend, database) into a detailed business report that business owners can read - every feature explained step by step, business rules, approval workflows, who can do what, and the information each form requires - plus a technical appendix that traces every statement to the code. Use when asked to "document this project", "extract features / business logic", "explain the system to the business owner", "what roles and permissions exist", "list all forms and required fields", "write a BRD/SRS from the code", or analyze an unknown system before a rewrite, audit, or handover.
allowed-tools: Bash(bash ${CLAUDE_SKILL_DIR}/scripts/inventory.sh *) Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/feature_ledger.py *)
---

# Codebase Business Analyzer

Turn source code into a **business report a non-technical owner can read and act on**: what the system does, how each process runs step by step, who is allowed to do what, what information must be entered, and what rules and approvals apply. Behind it, keep a **technical appendix** that proves every statement from the code.

The report must be **complete and deep**:
- **Complete** = every row of the *feature ledger* (Phase 1) is resolved. Choosing a subset ("this edition covers two processes") is not allowed.
- **Deep** = every feature gets a full feature card. A one-line catalog is not allowed either.

If you cannot finish in one session, do not shrink the work: save progress (ledger statuses + finished files) and end with `PARTIAL: X of Y ledger rows done — invoke the skill again to continue.` On the next invocation, continue from the first unfinished row instead of starting over.

## Project inventory (generated automatically when this skill loads)

!`bash ${CLAUDE_SKILL_DIR}/scripts/inventory.sh "${CLAUDE_PROJECT_DIR}" 25`

> If the block above shows the raw command instead of results (agents other than Claude Code, or shell execution disabled), run `bash <this-skill-folder>/scripts/inventory.sh <project-root> 25` yourself as the first step (`<this-skill-folder>` = the folder containing this SKILL.md, e.g. `.agents/skills/codebase-business-analyzer` for Codex). Use this inventory as your map and coverage checklist — do not re-explore the tree to rediscover what it already lists.

## Core rules

1. **Two audiences, two places.** The `business/` report is for owners: plain language, no file paths, no code words. The `technical/` appendix is for developers: citations, field names, mismatches. Every business statement must be backed by an entry in `technical/traceability.md` (feature ID → `file:line`).
2. **Explain, don't list.** Each feature is a full *feature card* (see Phase 5): purpose, who, when, numbered steps, required information, rules, approvals, and what happens afterwards. Write for a reader who has never seen the screens.
3. **Backend is the source of truth.** Frontend validation and hidden buttons are UX; backend guards, validators, and DB constraints are the real rules. Disagreements go to the technical findings, and to the business report only when they affect the business (e.g. "anyone can delete suppliers").
4. **Use the words the users see.** Take screen names, button labels, field labels and status names from the UI and its translation files (i18n / locale JSON), not from variable names. Use the Arabic labels from the translation files for the Arabic report when they exist.
5. **Never invent.** If the code doesn't tell you something (e.g. why a limit is 10,000), write "Not determined from the code" and add it to *Open questions*. Mark inferences `(inferred)` in the technical appendix.
6. **Read, never modify.** Read-only commands only — no migrations, seeders, installs, or writes to the analyzed project except the report folder.

## Workflow

Track progress with a checklist; large projects take several passes.

### Phase 1 — Reconnaissance

1. Start from the **Project inventory** above. If a category is capped at 25 and you need the rest, rerun the script with a larger limit.
2. Read the README, dependency manifests, env example, docker-compose, folder structure (2–3 levels).
3. Identify frontend, backend, ORM, database, auth mechanism, form libraries.
4. Load `references/stack-patterns.md` and read **only** the sections for the detected stacks.
5. **Find the other half of the system.** If this repo is frontend-only or backend-only, look for the sibling repo (`../*api*`, `../*back*`, `../*server*`, `../*front*`, a GraphQL schema or API base URL pointing to it). If found, analyze it **fully** (read-only), not as a spot-check. If not found, ask the user for its path once; if unavailable, state clearly in the report which conclusions come from the UI only.
6. **Build the feature ledger** — the definition of "complete". Pass every repo of the system (frontend and backend):
   ```bash
   python3 <this-skill-folder>/scripts/feature_ledger.py <frontend-repo> <backend-repo> --out docs/business-analysis/feature-ledger.md
   ```
   It lists every screen (router config, `<Route>`, file-based pages) and every backend operation (GraphQL mutations/queries, HTTP endpoints), grouped into candidate features, each row marked `⬜`. If the file already exists, the script keeps it: **resume** from its `⬜` rows. If the script finds nothing (unusual router style), build the same table by hand from the router, menu and API files.
7. Cross-check the ledger with the **navigation menu / sidebar config** and the permission list — anything the user can reach from the menu must be in the ledger; add missing rows by hand.
8. Turn the ledger into the **module list** (by business domain: Purchasing, Warehouses, Sales…) and the **feature list**:
   - One feature per distinct business document or outcome — "Stock transfer request" and "Stock issue request" are two features. If a draft description lists several documents joined by "and", split it.
   - Sub-screens of the same document (list, create/edit form, items view, report/print, workflow log, timeline) are **one** feature: mark them `➖ F07`.
   - Lookup/reference data (units, categories, statuses) are features too when users maintain them in a screen.
   - Mark technical rows `⛔ reason` (seeding, sync jobs, dev tools, upload URLs). A reason is mandatory.
9. Write the module/feature plan at the top of the ledger file (module → feature IDs) before writing any card, so the plan survives context limits.

### Phase 2 — Data model

From migrations, schema files, ORM models, GraphQL schema: entities, required fields, unique fields, relationships, multi-tenancy columns (company/branch/org), soft delete, and **every status/enum value** — statuses are the skeleton of the workflows.

### Phase 3 — Roles & permissions

Find every layer: role/permission definitions (enums, seeders, DB tables, permission constants), backend guards and policies, data-scope rules (who sees which records — by branch, company, creator), and frontend gating (route guards, menu config, permission hooks). Build the role × action matrix. Actions blocked only in the frontend are security findings.

If permissions are configured at runtime (stored in the DB and assigned by an admin), say so plainly to the business reader, list every permission that exists, and group them by screen and action.

### Phase 4 — Business logic & workflows

For every feature, trace from the screen to the backend handler to the DB:
- **Rules**: conditions, limits, calculations, defaults, uniqueness, dates, numbering, pricing/tax/discount, quantity checks (e.g. cannot issue more than the available balance).
- **Workflow**: statuses and every transition — who triggers it, preconditions, approvals, what it changes. Configurable workflow engines: document how configuration works and the default/seeded flow.
- **Effects**: stock balance changes, documents generated, notifications, emails, logs, effects on other modules.

### Phase 5 — Feature cards (the core of the business report)

Write one card per feature using the **Feature card** template in `references/output-templates.md`, module by module. After each module file is saved, update its ledger rows to `✅ F..` / `➖ F..` immediately. Every card must have all sections:

| Section | Must contain |
|---|---|
| What it is | 2–4 sentences: what it does and **why it matters to the business** |
| Who uses it | Roles / job titles, and who can only view |
| When it's used | The business situation that triggers it |
| How it works | Numbered steps from the user's point of view (usually 4–10) |
| Information required | Table: field label · required? · what it means / rules / allowed values. Include conditional requirements ("required when…") |
| Business rules | Plain sentences with real numbers, limits and conditions |
| Approvals & statuses | Lifecycle in plain words + simple diagram |
| What happens next | Effects on stock, money, other modules, notifications, generated documents |
| Reports & outputs | Printouts, exports, dashboards related to this feature |
| Notes & limitations | Things missing, risky, or needing confirmation |

If a section truly doesn't apply, write one sentence saying why (e.g. "No approval — the request is final once saved."). Empty or "N/A" sections are not allowed.

**Forbidden in `business/` files:** file paths, line numbers, component/route/mutation/query/endpoint/API/GraphQL/schema/DTO/enum/hook/state, code identifiers in backticks, and vague verbs without detail ("manage", "handle", "work with", "process" — say *create, edit, submit, approve, reject, cancel, print*).

### Phase 6 — Cross-module processes

Describe the end-to-end business processes as stories with a simple flowchart, e.g. *Purchase request → RFQ → Quotation comparison → Purchase order → Goods receipt → Stock addition*. For each step: who does it, what document is produced, what moves to the next step.

### Phase 7 — Export Markdown files

Always **write files to disk** — never leave the report only in chat. Templates: `references/output-templates.md`.

```
docs/business-analysis/
├── README.md                          # index, date, commit, scope, how to read
├── feature-ledger.md                  # coverage checklist (Phase 1) — every row resolved
├── en/
│   └── business/
│       ├── 01-executive-summary.md     # what the system is, main processes, key numbers, top risks
│       ├── 02-business-processes.md    # end-to-end processes (Phase 6)
│       ├── 03-features/<module>.md     # feature cards, one file per module
│       ├── 04-who-can-do-what.md       # roles in plain language + simple matrix
│       ├── 05-open-questions-and-risks.md
│       └── 06-glossary.md
├── ar/
│   └── business/                      # same files, same names, Arabic
└── technical/                         # English only, for developers
    ├── data-model.md                   # ER diagram, entities, statuses
    ├── permission-matrix.md            # full matrix with sources, data scopes, frontend-only checks
    ├── validation-reconciliation.md    # each form: frontend vs backend vs DB required fields
    ├── traceability.md                 # every feature ID / rule ID → file:line
    └── findings-and-gaps.md            # mismatches, risks, dead code, coverage
```

**Order to save tokens:** finish and verify `en/business/` and `technical/` first, then produce `ar/business/` by **translating the English files** — do not re-read the source code for Arabic.

**Arabic rules** (see *Arabic version* in `references/output-templates.md`):
- Translate everything in `business/`, including table headers, steps, statuses and diagram labels. Prefer the Arabic UI labels from the project's translation files.
- Keep feature/rule IDs (F01, BR1) unchanged so both versions and the appendix stay linked.
- First use of a technical term: Arabic then English in parentheses, e.g. أمر الشراء (Purchase Order).
- Modern Standard Arabic, clear and direct. Both versions state the same facts — same cards, same rows.

If the user asks for one language only, a different location, or a PDF/Word export, follow that instead.

### Phase 8 — Quality gate (do not skip)

- [ ] **Ledger is fully resolved** — this must print `0`, otherwise keep working (or end with the `PARTIAL:` line):
  ```bash
  grep -c '⬜' docs/business-analysis/feature-ledger.md
  ```
- [ ] Every `✅ F..` in the ledger has a matching card in `en/business/03-features/`, and every card ID appears in the ledger.
- [ ] Every module in the plan has its own file in `03-features/`; the executive summary's feature count equals the number of cards.
- [ ] Every feature card has all 10 sections filled with specifics (real field labels, real numbers, real status names).
- [ ] No business card describes more than one document type or outcome.
- [ ] Every status value has a place in a lifecycle.
- [ ] Every role appears in *Who can do what*.
- [ ] Run a leak check on business files and fix every hit (code words, file paths, backticks):
  ```bash
  grep -rniE '\.(tsx?|jsx?|php|py|cs|java)\b|mutation|graphql|endpoint|\bapi\b|component|schema|\bdto\b|\benum\b|`' docs/business-analysis/*/business
  ```
- [ ] **Owner test:** reread 3 random cards as a business owner who has never seen the code or screens. Could they explain the process to a new employee? If not, rewrite.
- [ ] Spot-check 5 claims in `technical/traceability.md` by reopening the cited lines.
- [ ] `en/business` and `ar/business` contain the same files and the same feature IDs.
- [ ] Final chat reply: file paths, counts (modules, features, roles, forms, open questions), and what was not covered — not the file contents.

## Scaling to large codebases

- Work module by module; write each module's cards and update the ledger as soon as they're done, so progress survives context limits.
- **More than ~15 features and the agent can run sub-agents/parallel tasks → use them.** Give each sub-agent one module: its ledger rows, the feature IDs, the paths of this skill's `references/output-templates.md`, the data model and roles list, and the rule to write a full card for every feature. Each returns only the path of its saved file. The main agent keeps the ledger, executive summary, processes and roles file, then checks every returned file against the ledger.
- Without sub-agents: one module at a time, save, update the ledger, continue. Never trade depth for breadth.
- Locate with search, then read only the relevant ranges. Skip generated files, `node_modules`, `vendor`, build output, lockfiles, minified assets.

## Asking the user

Ask only when it changes the output: the path of a missing backend/frontend repo, or a different audience/format than the default. Otherwise use the defaults above.
