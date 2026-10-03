# Jotaro to Storm 4 port research and tools

This is the source-and-documentation bundle for an experimental, offline Jotaro slot replacement. It contains authored Rust/Python/PowerShell/BAT code and phase reports only. It contains no extracted or generated game assets, CPK archives, binaries, game copies, or loader/API dependencies.

## Current result

A locally generated body candidate was installed as a loose Storm 4 file after user authorization, but the user's offline test showed Naruto unchanged. The mod has **not** been demonstrated to load in game. Animation export failed structural validation; no Storm moveset, voice, or SFX port is complete. Do not describe this as a playable character mod.

## Contents

- `out/rust/`: Rust CPK inventory/extraction/round-trip front end; delegates CPK operations to the community CPK Tool and does not decode inner XFBIN data.
- `out/phase3-work/*.py`: analysis, import/export, and parser-probe scripts used in the local Jotaro work. They expect Blender and community add-ons described in the phase notes.
- `out/phase5/`: local offline installer/launcher and hash-checked uninstaller. It installs a user-provided payload and starts the selected `NSUNS4.exe` directly; it does not call Steam.
- `PHASE*.md` and `NOTES.md`: findings, verification limits, and work history.

Generated assets and downloaded tools are deliberately excluded. Use assets from your own installations only. The scripts keep generated output under `out/` and should be reviewed before use.


## Stardust Storm (run 1)

Start with [PROGRESS.md](PROGRESS.md), [USER_TEST_CARD.md](USER_TEST_CARD.md), [FOUNDATION_REPORT.md](FOUNDATION_REPORT.md), and [FINAL_REPORT.md](FINAL_REPORT.md). New code lives in `scripts/`, `tools/stardust-tools/`, `installer/`, and `mod/config/`.
