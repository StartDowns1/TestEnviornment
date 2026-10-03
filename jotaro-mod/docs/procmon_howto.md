# ProcMon card — does Storm 4 even look for our loose file? (B7)

Process Monitor (Sysinternals, from Microsoft) only **observes** file access. It does not touch the game, DRM, or memory.

1. Download Process Monitor from Microsoft Sysinternals, then run `Procmon64.exe` **as administrator**.
2. Capture starts on its own. Press **Ctrl+E** to stop it, then **Ctrl+X** to clear the list.
3. **Filter > Filter...** and add these two rules (Include):
   - `Process Name` `is` `NSUNS4.exe`
   - `Path` `contains` `data_win32`
   Then click Apply/OK.
4. Install the rung you are testing with the installer, then start the game the same way as before (`LAUNCH_METHOD`).
5. Press **Ctrl+E** to start capturing. Go to Free Battle, pick the slot (Naruto for 1nrt), and load into the battle.
6. Press **Ctrl+E** to stop. Look for rows ending in `\data_win32\spc\1nrtbod1.xfbin` and note the **Result** column:
   - `SUCCESS` on a `CreateFile` row: the game opened our file. The problem is content (C2/C3/C4).
   - `NAME NOT FOUND` / `PATH NOT FOUND`: it looked, but somewhere else or under another name. Compare the exact path.
   - **No rows at all**: it never looked under `data_win32` (C1).
7. **File > Save...**, choose *Events displayed using current filter*, format **CSV**, and save to `<project>\out\logs\procmon-L0.csv` (or `-L1`, ...).
8. Run: `python scripts\summarize_procmon.py out\logs\procmon-L0.csv`. Paste its output into `RUNTIME_RESULTS.md`.

**Bonus capture (very informative):** repeat with only the `Process Name` rule plus `Path contains 1nrt`. This shows which Naruto files the game opens, and from where (CPK vs. loose). Run the summarizer with `--filter 1nrt`.
