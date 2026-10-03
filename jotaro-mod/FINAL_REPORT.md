# FINAL REPORT — Stardust Storm run 1

## Headline
This run had **no access to either game, the dio_port payload, the extracted catalogs, the community tools, or Blender**. It was a Linux cloud container holding only this git repo. So **Goal 0 is not answered with new evidence.** No UI, art or character payload was produced. Nothing here "works" in game; nothing was tested in game.

What *was* built is the foundation the next session needs:
- the evidence-gathering scripts;
- a safer installer that can run the L0 control test today;
- a config-driven build;
- the asset guard.

## Built (status words per PROGRESS.md)
| Item | Status | How verified |
|---|---|---|
| `scripts/check_no_assets.py` + local pre-commit hook | DONE-VERIFIED-OFFLINE | rejected staged dummy `.xfbin` and `out/foo.txt`; unit tests; ran on every commit of this run |
| `.gitignore` extension | DONE-VERIFIED-OFFLINE | `git check-ignore -v` on samples |
| Doc link fixes, root README, duplicate-launcher hashes | DONE-VERIFIED-OFFLINE | grep + SHA-256 (identical) |
| `mod/config/stardust.toml` | DONE-VERIFIED-OFFLINE | parsed by tomllib and `stardust build` |
| `tools/stardust-tools` (`stardust findstr / magic / build / manifest`) | DONE-VERIFIED-OFFLINE | 5 cargo tests: planted strings in 4 encodings, magic/entropy, manifest SHA-256 of "abc", output guard, collision and overlong-string refusal, per-rung manifests |
| `installer/stardust.ps1` + `Stardust.bat` | DONE-VERIFIED-OFFLINE (mock) | `installer/test_installer.ps1`: 14/14 on PowerShell 7.4.6 (dry-run, OFFLINE gate, tampered payload, set conflicts, originals gate, changed-file protection, retry, byte-exact restore, running-process refusal). Windows PowerShell 5.1 untested. |
| `scripts/summarize_procmon.py` + `docs/procmon_howto.md` | DONE-VERIFIED-OFFLINE | fixture test |
| `scripts/decode_storm_entry.py`, `xfbin_inventory.py`, `stage_ladder.py`, `blender/l1_storm_roundtrip.py` | written, syntax-checked; **not run** (need local files) | `py_compile`; stage → build → dry-run install verified end to end with a fake rung |
| FOUNDATION_REPORT.md | hypotheses only | — |

## Only you can confirm
L0 Dio control, ProcMon access, L1 giant Naruto. See USER_TEST_CARD.md.

## BLOCKED / not done
B1–B4, the rungs themselves, C2–C5, D, E1/E2/E4, F, and the U1 rung. All need game files. **Not guessed:** Storm slot codes for Sasuke/Lee/Kakashi, UI text format, bone mapping. Assumptions are in DECISIONS.md.

## Commands
```
cd tools\stardust-tools; cargo build --release; cargo test; cd ..\..
python scripts\tests\test_scripts.py
stardust build --config mod\config\stardust.toml [--profile ladder|ui-only|ui-plus-characters]
installer\Stardust.bat -Action install -GameRoot "<Storm4>" -Payload out\payload\ladder\L0 -Set L0 -DryRun
installer\Stardust.bat -Action install -GameRoot "<Storm4>" -Payload out\payload\ladder\L0 -Set L0
installer\Stardust.bat -Action status
installer\Stardust.bat -Action uninstall [-Set L0] [-DryRun]
pwsh installer\test_installer.ps1        # mock tests, never touches the real game
```

## Next steps (bring this to a new session, on your PC or with the files uploaded)
1. Uninstall the old Jotaro file. Run test card steps 1–2 (L0 + ProcMon). Fill in RUNTIME_RESULTS.md (Appendix B format).
2. Run test card step 3 (decode the Naruto body, dio_port anatomy, chunk diff, rig compare). Commit only the structure-only `docs/*.md` it writes.
3. Resume at B1 with that evidence. Then: L1 → the branch at B6 → Stage C text work (`stardust findstr` is ready) → F re-skin using the real B2 bone names.
4. Record `out\tools\*` hashes in docs/TOOLS.md.

## G5 hygiene
The asset guard passed over the whole branch diff. Only allowlisted legacy code is tracked under `out/`. Pushed only to `claude/stoic-cray-1p7g5j`; no PR was opened.
