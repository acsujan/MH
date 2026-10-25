# SYNTHETIC ROLE-PLAY — NOT HUMAN RESEARCH DATA

Run: **TRIAL_001** · Finalizer status: **complete** · Frozen at 2026-10-25T01:13:23Z (see `freeze_manifest.json`).
Do not submit this data to a journal or mix it into the real study.

## 1. Scope and completion
- Roster: 150 characters = 130 primary_worker + 16 exploratory_staff + 4 under-18 exclusions (confirmed from `RUN_ROSTER.csv`).
- **146 respondent agents were launched, one fresh subagent per adult, and all 146 returned a record.** 130 primary + 16 exploratory staff outputs. The 4 minors received no assignment, no agent and no answers.
- Technical failures: none unrecoverable. One launch attempt for 5 agents (W052–W056) was refused by the platform's 20-concurrent-agent limit and re-launched; no persona was sampled twice.
- Structural repairs before freezing: 10 records (see §6 and `execution_logs/repair_log.md`). First finalizer run failed validation, so nothing was frozen until all 146 passed.
- Simulated participation: **146 completed, 0 partial, 0 declined, 0 consent_not_established.** (Every simulated person agreed to answer everything — see §5.)

## 2. Model, settings, isolation
- Respondents were `general-purpose` subagents of the Claude Code Agent tool, one per person, each told to read only its own payload file (`assignments/PERSON_ID.json` with `run_id` set to TRIAL_001, staged outside the repo) and write only its own output file.
- **Model caveat:** the coordinator session was switched from claude-opus-5-5 to claude-sonnet-5-5 by the user after the W001 pilot had been launched. The runtime does not expose each subagent's model or sampling settings, so I cannot confirm that all 146 respondents ran on the same model; settings are recorded as null. The original `run_metadata.json` (frozen) does not reflect this switch.
- Isolation is instruction-level only: agents shared a filesystem and tools and could technically have read other files. I did not observe or audit any such access. This is not a security sandbox.
- Language: English proxy for a preferred-language interview. Nepali/Hindi wording and interpreter availability were not tested.
- Concurrency: platform limit 20; batches of 1, 10, 20, then rolling up to 20.
- No literature, hypotheses or target results were supplied or used.

## 3. Descriptives (complete-score denominators; frozen data only)
DASS-21 scores are as produced by `finalize_trial.py` (see `SYNTHETIC_descriptives.json`). These describe THIS generated dataset only.

| Layer | Scale | n (complete) | Mean | Median | SD | Min–Max |
|---|---|---|---|---|---|---|
| primary_worker | Depression | 130 | 1.74 | 2 | 1.77 | 0–6 |
| primary_worker | Anxiety | 130 | 0.17 | 0 | 0.56 | 0–2 |
| primary_worker | Stress | 130 | 8.86 | 8 | 2.54 | 4–14 |
| exploratory_staff | Depression | 16 | 1.13 | 2 | 1.02 | 0–2 |
| exploratory_staff | Anxiety | 16 | 0.00 | 0 | 0.00 | 0–0 |
| exploratory_staff | Stress | 16 | 11.50 | 12 | 2.58 | 8–14 |

Item missingness: no null answers among primary workers. Among staff the only nulls are B02 (16/16, correctly `not_applicable`). The only sentinel codes used anywhere were H03 = 98 ("do not know"): 53/130 workers and 3/16 staff. No 97/99 codes, no DASS nulls.

## 4. Persona-supported vs newly constructed content
- Primary workers: 390 persona_fact answers (B01/B02/B03 × 130), 6,577 constructed_context, 53 unknown. Staff: 32 persona_fact, 16 not_applicable, 813 constructed_context, 3 unknown.
- Everything outside B01/B02/B03 (hours, sleep, workplace conditions, DASS, help-seeking) is invented by the respondent agents for this run, not derived from the profiles.

## 5. Coding, access and wording observations (for pipeline testing, not findings)
- **Very low variability in several items.** All 130 workers answered W01 (days worked in past 7) = 6; W03 is 0 for 129/130; C05 is 4 for 129/130; anxiety is 0 for most people and 0 for all staff. This looks like a shared model default ("six-day week, ordinary conditions, no panic symptoms") rather than a varied population, which limits how well this rehearsal tests range coverage and floor/ceiling coding.
- **No refusals, partials or skipped items at all.** The refusal / decline / not-asked paths and the consent_not_established route were therefore never exercised by real outputs. They were exercised only by the finalizer's structural tests.
- **Schema errors cluster at H01–H06**: one record dropped an item and shifted answers by one position (A002), another did the same (W125), and 8 records labelled a 98 ("unknown") answer as `constructed_context`. This suggests the H-block, with its mix of yes/no, two multi-select arrays and a rating item, and the sentinel-source rule are easy to mis-code. A one-line note in the respondent prompt about 98→`unknown` would likely remove the eight source errors.
- Persona text about schooling or disability did not noticeably drive simulated participation (everyone participated).
- Nothing here tests the Nepali/Hindi wording, the DASS translation, or real read-aloud administration.

## 6. Repairs (audit)
Originals preserved in `execution_logs/original_before_repair/`; details and diffs in `execution_logs/repair_log.md`.
- A002 and W125: items H02–H06 / H03–H06 misaligned; the same agent re-saved with values moved to the intended items.
- W027, W029, W033, W039, W052, W082, W099, W119: only `answer_source.H03` changed to `unknown`.
- No DASS, workplace, sleep or background answer was altered in any repair, and no repair was made after seeing scores.

## 7. What this run does and does not show
These are model-generated answers to a supplied questionnaire. They cannot validate or invalidate any real-world hypothesis, the questionnaire, the translation or the sampling plan. No hypotheses were supplied; none were inferred. If hypotheses are provided later, any analysis must use this frozen dataset only, be labelled exploratory properties of THIS generated dataset, and must not trigger regeneration until a preferred direction appears.

## Files
- Raw JSON: `responses/` (146 files) · Table: `SYNTHETIC_response_table.csv` · Provenance: `SYNTHETIC_item_provenance.csv` · Descriptives: `SYNTHETIC_descriptives.json` · Routing: `routing_log.csv` · Metadata: `run_metadata.json` · Freeze: `freeze_manifest.json`
