# Main log (DAIV-LANG v001)

## Block 0, 2026-10-23

- Start approx. 18:07:41 UTC (first record), run by the author: `driver.py run ... --repeat 0`.
- Check against `FREEZE.md` on the first 90 records: `perplexity/sonar` via Perplexity (60),
  `openai/gpt-6-luna` via OpenAI (30); consistent with the frozen configuration. 0 errors so far.
- The default models in the apps were not rechecked in the release notes before block 0
  (status as in PROTOCOL.md §4, sources from 2026-10-23). `[SOURCE NEEDED]` remains.
- The next block (`--repeat 1`) no earlier than 60 min after the end of block 0.

**Block 0 completed:** 120/120 ok, 0 errors. Call starts 18:07:41–18:16:44 UTC.

## Block 1, 2026-10-23

- Start 19:21:20 UTC, gap from the last start of block 0 approx. 64 min (≥ 60 min, as required by FREEZE).
- Completed: 120/120 ok, 0 errors. Call starts 19:21:20–19:25:56 UTC.

## Block 2, 2026-10-23

- 120/120 ok, 0 errors. Call starts 20:50:26–20:54:43 UTC; gap from block 1 approx. 84 min.
- Status after three blocks: 360/600, 0 errors, all three blocks on the same day.

## Block 3, 2026-10-23

- 120/120 ok, 0 errors. Call starts 21:55:04–21:59:36 UTC; gap from block 2 approx. 60 min
  (last start of block 2 at 20:54:43, first of block 3 at 21:55:04).
- Status after four blocks: 480/600, 0 errors.

## Block 4: aborted attempt, 2026-10-23

- The author started `--repeat 4` at 22:53:05 UTC, approx. 53 min after the last start of block 3
  (21:59:36), i.e. before the minimum gap of 60 min. Interrupted with Ctrl-C after 5 calls
  (all `or-pplx`, starts 22:53:05–22:53:09).
- These 5 records were moved from `raw/` to `aborted-block4-20261023T2253Z/` (not deleted).
  They are not part of the analysis; the entries in `ledger.jsonl` remain as a trace. Block 4 will be
  rerun from scratch with the full set of 120 slots, no earlier than 22:59:36 + a margin.

## Block 4, 2026-10-23

- 120/120 ok, 0 errors. Call starts 23:00:30–23:04:10 UTC; gap from block 3 approx. 61 min.
- **Main complete:** 600/600, 0 errors, five blocks on 2026-10-23 (UTC), gaps of 64, 84, 60, 61 min.
  `perplexity/sonar`/Perplexity 300, `openai/gpt-6-luna`/OpenAI 300.
