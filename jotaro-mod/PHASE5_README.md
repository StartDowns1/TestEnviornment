# Phase 5 — local launcher, payload, and restore

## Current package

`out/phase5/payload/data_win32/spc/1nrtbod1.xfbin` contains the generated Jotaro body-only test. It is a local generated asset, excluded from Git. The same file has already been copied to the supplied Storm 4 folder as a new loose override; no archive was repacked.

- Double-click `Launch_Jotaro_Mod.bat` to install/verify the local payload and start `NSUNS4.exe`.
- Type `OFFLINE` exactly when asked. The launcher does not provide online-mode support.
- Press Enter to accept the remembered Storm 4 folder. If it is wrong, enter the folder containing `NSUNS4.exe`; if necessary, the launcher then asks for the executable path.
- The default payload is included under this folder. If it is missing, enter a folder containing `data_win32`.
- The payload targets the Naruto `1nrt` body slot. The user's first offline test showed Naruto unchanged, so the loose-file override has not been proven to load. Do not interpret the launcher completing as a successful in-game mod test.

## Restore / uninstall

1. Close Storm 4.
2. Double-click `Uninstall_Jotaro_Mod.bat`.
3. Press Enter to accept the recorded game folder, or enter the game folder used for installation.

The script restores an original override from a hash-checked backup if one existed before installation. In the current install, the target did not exist, so uninstall removes only `data_win32/spc/1nrtbod1.xfbin` if its hash still matches the installed payload. It also removes only the empty directories this project created. If the target changed after installation, it leaves that file alone and retains the install record for manual resolution. Backups stay under `out/phase5/backups/`.

## Other actions

`modctl.ps1 install` installs the payload without starting the game; `modctl.ps1 launch` (the batch file's action) installs and starts Storm 4. Both require the explicit offline confirmation and a closed game process. `modctl.ps1 uninstall` restores the recorded state and requires Storm 4 to be closed.

The PowerShell syntax and install/uninstall flows were checked against disposable mock folders under `out/`: file hashes, created-directory cleanup, hash-checked backup restore, protection of a changed file, and retry after a conflict all passed. No game process was started during these checks.

The scripts never repack a CPK, edit an original game file, communicate with Steam, touch DRM/anti-cheat components, or select an online mode. The first runtime test showed no visible replacement; loose-file precedence and model appearance are not runtime-verified. See [Phase 3](PHASE3_PROGRESS.md), [Phase 4](PHASE4_PROGRESS.md), and [running notes](NOTES.md) for current limits.

