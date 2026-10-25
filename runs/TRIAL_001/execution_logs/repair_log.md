# Repair log — TRIAL_001

## A002 (exploratory_staff)
- Problem: `answers` lacked key H06 while `answer_source` had it; the H02–H05 values were offset by one position (H03 held an array `[1, 4]`, H04 `[1, 2]`, H05 `3`).
- Action: original preserved at `execution_logs/original_before_repair/A002.json`. The same A002 agent was sent one minimal request naming the schema problem (missing H06) and asked to change nothing else.
- Result: the agent realigned H02–H06 to 0, 1, [1,4], [1,2], 3. The values that were already in the original were moved to their intended items; no score-relevant (DASS/C/P/W) answer changed. Checked by diffing original vs repaired: only H02–H06 differ.
- Not a decline; an execution/formatting error. No resampling.

## Other notes
- A launch attempt for W052–W056 was refused by the platform's 20-concurrent-agent limit; those five were launched later. No respondent was run twice.

## Pre-freeze validation repairs (finalizer run 1 failed; nothing was frozen)
Originals of all repaired files: `execution_logs/original_before_repair/`. Each repair was a minimal request to the same person's agent, naming only the schema problem. Diffs (original vs repaired) were checked afterwards.

| Person | Problem | Change made |
|---|---|---|
| A002 | H06 missing from `answers`; H02–H05 offset by one position | H02–H06 realigned (see above) |
| W125 | H03–H06 offset by one position / wrong types (scalar for H04/H05, array for H06, sentinel without matching source) | H03→98(unknown), H04→[1,2], H05→[1,5], H06→2 |
| W027, W029, W033, W039, W052, W082, W099, W119 | H03 = 98 with source `constructed_context` (contract requires `unknown`) | `answer_source.H03` set to `unknown`; no answer value changed |

No DASS, workplace, sleep or background answer was changed in any repair.
