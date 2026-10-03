# TestEnviornment

## Jotaro / Stardust Storm port project

The authored code and phase documentation are in [jotaro-mod/README.md](jotaro-mod/README.md). Generated and extracted game assets are excluded and must never be committed (see `jotaro-mod/scripts/check_no_assets.py`).

### Duplicate launcher copy

`mods/jotaro-offline-launcher/` duplicates the launcher scripts in `jotaro-mod/out/phase5/`. Checked 2026-10-03 with SHA-256; all three files are byte-identical:

| File | SHA-256 (both copies) |
|---|---|
| `modctl.ps1` | `3EB15E7D7664488F57EF9DDB8A5E1299CA53AA22293DFE5BF84236862679F4B9` |
| `Launch_Jotaro_Mod.bat` | `3AF9C37BA3417374864EB1D3EFFAE390EA9BDD228E7AE5CD909280D2FABEAC55` |
| `Uninstall_Jotaro_Mod.bat` | `AC961CE207BF6CAD68AE51A44CB5498AACD1F2DE5E0E4512CFE44132FF959ADC` |

Nothing was deleted. The new installer is in `jotaro-mod/installer/`.
