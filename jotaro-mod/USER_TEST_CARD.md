# USER TEST CARD — Stardust Storm run 1

Do these in order; the fastest answers come first. All commands run from the `jotaro-mod` folder in PowerShell. **Offline only.** Close Storm 4 before any install or uninstall.

One-time build of the tools: `cd tools\stardust-tools; cargo build --release; cd ..\..`
(The binary is `tools\stardust-tools\target\release\stardust.exe`, called `stardust` below.)

## 0. Remove the old Jotaro install first
Run `out\phase5\Uninstall_Jotaro_Mod.bat`. It removes `data_win32\spc\1nrtbod1.xfbin` if the hash still matches. This keeps the test clean.

## 1. L0 — Dio control (most important)
```
python scripts\stage_ladder.py L0 "<your Downloads>\dio_port\data_win32"
stardust build --config mod\config\stardust.toml --profile ladder
installer\Stardust.bat -Action install -GameRoot "<Storm 4 folder>" -Payload out\payload\ladder\L0 -Set L0 -DryRun
installer\Stardust.bat -Action install -GameRoot "<Storm 4 folder>" -Payload out\payload\ladder\L0 -Set L0
```
- **Reach it:** launch the same way as last time. Go to Free Battle and pick the slot dio_port replaces. Check `docs/dio_port_anatomy.md` once B3 has run; otherwise try the character whose code matches `1tmr` and any `1dio` names.
- **Success:** Dio appears. Loose-file loading works in your install, so the Jotaro problem is content or naming (C2/C3/C4).
- **Failure — nothing changes:** the stock game probably doesn't read `data_win32` loose files (C1). Next session builds Variant B (Modding API / CPK).
- **Failure — crash:** write down the screen and the moment. Next session prepares a bisect.
- **Paste back:** `DIO_CONTROL`, `DIO_CONTROL_NOTES`, `LAUNCH_METHOD`.
- **Undo:** `installer\Stardust.bat -Action uninstall -Set L0`

## 2. ProcMon check (do it during step 1)
Follow `docs/procmon_howto.md`, then run `python scripts\summarize_procmon.py out\logs\procmon-L0.csv`.
**Paste back:** `PROCMON_1NRTBOD1` (or the Dio file equivalent) and the summarizer output. Also record which Naruto you picked (`NARUTO_COSTUME_TESTED`).

## 3. Evidence scripts for the next session (no game launch needed)
```
python scripts\decode_storm_entry.py find out\phase2-work 1nrtbod1
python scripts\decode_storm_entry.py decode "<Storm4>\data\launch\data1.cpk" <entry path printed above> out\stardust\storm-naruto-decoded\1nrtbod1.xfbin
python scripts\xfbin_inventory.py inventory "<Downloads>\dio_port\data_win32" --json out\stardust\dio_port.json --md docs\dio_port_anatomy.md
python scripts\xfbin_inventory.py diff out\stardust\storm-naruto-decoded\1nrtbod1.xfbin "<dio_port>\data_win32\spc\<dio body>.xfbin" out\phase5\payload\data_win32\spc\1nrtbod1.xfbin --md docs\chunk_diff.md
blender -b --python out\phase3-work\compare_jotaro_naruto_rigs.py -- out\phase3-work\asbr-jotaro\spc\2jsp01bod1.xfbin out\stardust\storm-naruto-decoded\1nrtbod1.xfbin out\stardust\rig_compare.json
```
`dio_port_anatomy.md` holds structure only (names, sizes, hashes, chunk types) and is safe to commit. Check it before committing anyway.

## 4. L1 — giant Naruto (needs step 3's decoded file)
```
blender -b --python scripts\blender\l1_storm_roundtrip.py -- out\stardust\storm-naruto-decoded\1nrtbod1.xfbin out\stardust\L1\1nrtbod1.xfbin
python scripts\stage_ladder.py L1 out\stardust\L1\1nrtbod1.xfbin spc\1nrtbod1.xfbin
stardust build --config mod\config\stardust.toml --profile ladder
installer\Stardust.bat -Action install -GameRoot "<Storm 4 folder>" -Payload out\payload\ladder\L1 -Set L1
```
- **Success:** Naruto is 1.4× bigger. The exporter and the loose mechanism are sound, so Jotaro's content is the problem (C3).
- **Failure:** Naruto is normal size: the mechanism or the exporter is at fault. A crash means the exporter output is rejected.
- **Paste back:** `L1: OK | wrong | crash` plus notes.

## 5+. Build stamp, renamed menus, art, other characters
Not built in this run. They need the UI text format and texture locations (Stages C–E), which need game files. See FINAL_REPORT.md.
