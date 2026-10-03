# PROGRESS — Stardust Storm run 1

## State summary (A1)
1. The project ports ASBR Jotaro (`2jsp01`) into Storm 4's Naruto slot (`1nrt`) as a loose `data_win32/spc/1nrtbod1.xfbin`.
2. First in-game test: Naruto unchanged. The cause is unknown; see FOUNDATION_REPORT.md.
3. RUNTIME_RESULTS.md does not exist, so B6 follows the `not_run` branch.
4. **This run's environment:** a Linux cloud container with only the git repo. It has no game installs, catalogs (`out/phase2-work`), community tools (`out/tools`), Blender, or dio_port. The Windows Steam path you gave cannot be reached from here.
5. Consequence: every task that needs game bytes is BLOCKED, with a ready-to-run script and the exact command in USER_TEST_CARD.md.
6. Tracked code: `out/rust` (CPK CLI via cpk-tool), `out/phase3-work/*.py` (Blender scripts), `out/phase5` (old launcher).
7. `mods/jotaro-offline-launcher` is byte-identical to `out/phase5` (hashes in the repo-root README).
8. The vanilla Storm Naruto body was never decoded. CPK Tool returns stored (compressed) bytes. The CRILAYLA probe's outcome was never recorded.
9. The animation candidate failed both readers and is not in any payload.
10. New this run: asset guard plus hook, extended `.gitignore`, `stardust.toml`, the `stardust-tools` crate, the new installer with 14 passing mock tests, and evidence scripts.
11. Docs/code disagreements found and fixed: links to `rust/` → `out/rust/`; `out/PHASE5_README.md` → `PHASE5_README.md`.
12. Disagreement noted (not fixed in legacy code): `probe_xfbin.py` hardcodes sample paths under `out/phase3-work/`. The new `scripts/xfbin_inventory.py` takes paths as arguments.
13. Disagreement noted: PHASE5 says the payload was installed "after user authorization" by the assistant, while the prompt says installation is by the user. The new installer is user-run only.
14. `modctl.ps1` remembers the game root in `out/phase5/install-state.json`. The new installer reuses it when present.
15. Old `modctl.ps1` uses `\` separators (Windows only). The new installer is separator-neutral and was tested under PowerShell 7 on Linux.
16. The `data_win32/` prefix is borrowed from dio_port. CPK-internal paths use `data/`. This is a key open question (C1).
17. The ASBR non-NUCC patch entries (`54 09 41 02`, `23 FB 57 04`) are still unresolved.
18. No game assets are in git. The guard enforces this on every commit.
19. Branch: `claude/stoic-cray-1p7g5j` (harness-mandated, pushed). See DECISIONS.md.
20. Next session: run USER_TEST_CARD steps 0–3, fill in RUNTIME_RESULTS.md, then resume at B1.

## Tasks
| ID | Status | Notes |
|---|---|---|
| A1 | DONE-VERIFIED-OFFLINE | summary above |
| A2 | DONE-VERIFIED-OFFLINE | dummy `.xfbin` and `out/foo.txt` rejected by script and by hook; unit tests in `scripts/tests` |
| A3 | DONE-VERIFIED-OFFLINE | `git check-ignore -v` on sample paths; legacy code not ignored |
| A4 | DONE-VERIFIED-OFFLINE | links fixed; root README cleaned; duplicate hashed (identical) |
| A5 | DONE-VERIFIED-OFFLINE | parsed by tomllib and by `stardust build` |
| B1 | BLOCKED | no Storm CPK/catalog here. Script `scripts/decode_storm_entry.py` is ready (stores stored + decoded payloads, runs the CRILAYLA probe). Needs: run on the user's PC (test card step 3). |
| B2 | BLOCKED | needs B1 + Blender; command in test card step 3 |
| B3 | BLOCKED | dio_port not present. Needs: run `scripts/xfbin_inventory.py inventory` on the user's PC. Q1–Q5 unanswered. |
| B4 | BLOCKED | needs B1+B3; `scripts/xfbin_inventory.py diff` ready |
| B5 | DONE-VERIFIED-OFFLINE (tooling) / BLOCKED (rungs) | `stage_ladder.py` + per-rung build + installer verified end to end with a fake rung. L0/L1 need local files; L2/L3 need B4/B2. |
| B6 | DONE-VERIFIED-OFFLINE | `not_run` branch taken: L0 first on the test card |
| B7 | DONE-VERIFIED-OFFLINE | `docs/procmon_howto.md`; summarizer tested on a fixture |
| B8 | DONE-UNVERIFIED-IN-GAME | FOUNDATION_REPORT.md (hypotheses ranked; no new evidence) |
| C1 | DONE-VERIFIED-OFFLINE | `stardust findstr`; planted-string unit test (UTF-8/16LE/16BE/Shift-JIS) |
| C2–C5 | BLOCKED | need decoded game files; strings pre-listed in `stardust.toml` (`max_len` unknown) |
| D1–D4 | BLOCKED | need game textures/GFX and Pillow on the user's PC |
| E1–E2, E4 | BLOCKED | need the `.gfx` files + JPEXS |
| E3 | DONE-VERIFIED-OFFLINE | `-AllowModifyOriginals` + typed confirmation + backup/restore covered by mock tests. Steam fallback: Library > Storm 4 > Properties > Installed Files > *Verify integrity of game files*. U1 rung not built. |
| F1–F5 | BLOCKED | need catalogs/assets/Blender. Re-skin pipeline not written (depends on B2's real bone names; not guessed). |
| G1 | DONE-VERIFIED-OFFLINE | `stardust build`; unit tests + empty-profile refusal |
| G2 | DONE-VERIFIED-OFFLINE | `installer/stardust.ps1` + `Stardust.bat` |
| G3 | DONE-VERIFIED-OFFLINE | `installer/test_installer.ps1`: 14/14 pass (PowerShell 7.4.6, mock folders under `out/`). Windows PowerShell 5.1 not tested. |
| G4 | DONE-VERIFIED-OFFLINE | USER_TEST_CARD.md |
| G5 | DONE-VERIFIED-OFFLINE | see FINAL_REPORT.md |
| G6 | DONE-VERIFIED-OFFLINE | FINAL_REPORT.md |
