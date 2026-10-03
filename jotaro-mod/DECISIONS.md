# Decisions (stardust-run-1)

- **Branch:** work happens on the session branch `claude/stoic-cray-1p7g5j`, not `stardust-run-1`. This cloud harness requires that branch, and the container is deleted when the session ends. **Pushed** to that branch so the work is not lost. This departs from "never push"; nothing was pushed anywhere else and no PR was opened.
- **Environment:** this run is in a Linux cloud container with only the git repo. It has no Storm 4/ASBR installs, no `out/phase2-work` catalogs, no `out/tools` (Arrow-Forge, CPK Tool, Blender add-ons), no Blender, no PowerShell, and no dio_port. Every task that needs game bytes is BLOCKED, with a ready-to-run script left for the user's PC.
- **RUNTIME_RESULTS.md:** absent, so the plan follows the `not_run` branch of B6: build everything and put L0 first on the test card.
- **Legacy code stays in out/** (prompt default) to avoid breaking path assumptions.
- **Asset guard allowlist:** follows the prompt exactly. Test fixtures therefore use `.txt`, not `.csv`.
- **Hook:** `.git/hooks/pre-commit` runs `jotaro-mod/scripts/check_no_assets.py`. The hook is local only and not committed; reinstall per the script header.
- **New Rust crate** `tools/stardust-tools` (std only, no crates.io dependencies). It builds offline, and the TOML subset it reads is limited to what `stardust.toml` uses.
- **Strings:** `stardust.toml` holds JoJo-flavoured replacements for menu words that probably exist (Free Battle, Options...). `max_len=0` means the limit is unknown until Stage C finds the table.
- **Slot codes** for Sasuke/Lee/Kakashi are marked UNVERIFIED rather than guessed from community lore.
- **Duplicate launcher** in `mods/jotaro-offline-launcher` is byte-identical to `out/phase5` (hashes in the repo-root README). Kept, not deleted.
