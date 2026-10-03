# Jotaro slot-replacement installer/launcher (offline, experimental)

This repository package contains only the local installer/launcher scripts. It does **not** include game files, extracted assets, the generated XFBIN model, or any Steam, DRM, anti-cheat, or game-mod API binaries.

## Status

The local Jotaro body candidate is experimental. In the first offline test, Naruto appeared unchanged. The current loose-file approach and model are therefore **not verified in game**. This launcher does not make the mod load; it only copies the selected payload, tracks hashes/backups, starts `NSUNS4.exe` directly, and can restore the files it installed.

## Use

1. Put a locally generated mod payload in a folder whose structure includes `data_win32` (for example `data_win32\spc\1nrtbod1.xfbin`). Obtain/generate game assets only from your own installation; no game asset is distributed here.
2. Run `Launch_Jotaro_Mod.bat` and type `OFFLINE` at the prompt.
3. Enter the Storm 4 folder containing `NSUNS4.exe`, then the payload folder containing `data_win32`.
4. The script launches the executable directly from that folder. It does not connect to or launch Steam.

Use only offline. The mod payload must be closed before uninstalling. Run `Uninstall_Jotaro_Mod.bat` to remove only files whose hashes still match the installed payload, or restore hash-verified backups. Files changed since installation are left untouched.

Install records and backups are created beside the scripts at runtime. Review the scripts before use.

