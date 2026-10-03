# Running notes

## 2026-10-02 — Phase 1 recon

- Inventory/signature notes and feasibility verdicts: [PHASE1_FINDINGS.md](PHASE1_FINDINGS.md).
- Both game trees include many `.cpk` archives; samples have CRI `CPK ` headers. Loose XFBIN samples start with `NUCC`.
- Storm 4 candidates: loose `data_win32` overrides and a community modding API that loads prioritized custom CPKs. Runtime precedence has not been tested.
- Supplied `dio_port/data_win32` is a pre-existing mod payload with `spc` and `spcload` paths; no parsing or copying performed.
- No game files changed. No game assets have been copied into project output.
- Outstanding at Phase 1: inspect archive tables and XFBIN chunk inventories; verify CPK entry compression and any encryption; identify comparable character assets; test conversion and runtime in an offline user-controlled install.

## 2026-10-02 — Phase 2 reader/extractor

- Rust CLI source/build notes: [rust/README.md](rust/README.md).
- Phase 2 results and round-trip hashes: [PHASE2_RESULTS.md](PHASE2_RESULTS.md).
- Generated catalogs, extracted game files, tool binaries, and build outputs live under ignored `out/phase2-work`, `out/tools`, and `out/rust/target`; they are local-only and must not be committed.
- Rust CLI catalog completed both supplied trees: ASBR 36 CPK + 5 loose XFBIN; Storm 4 29 CPK + 9 loose XFBIN; zero archive listing failures.
- Exact extraction/repack SHA-256 comparisons passed for ASBR patch120 (34 files), Storm 4 DLC5 data.cpk (37 files), and Storm 4 DLC10 data.cpk (2 files).
- ASBR patch120 entries `data/spc/3dio01prm.bin.xfbin` and `data/skill/7dio01_x.xfbin` did not begin with `NUCC`; inner encoding/encryption status remains unknown. They were not decoded or altered.
- Correction: CPK Tool extracts stored CPK entry payloads for compressed entries. For patch120 `data/skill/3hhs01_x.xfbin`, catalog lists 183.59 KB / 12.45 KB, while extraction produced 12,752 bytes. Exact repack proves entry/container preservation, not game-facing decompression or loadability.

## 2026-10-02 — Phase 3 Jotaro body proof of concept

- The user selected Jotaro (`2jsp01`) for the one-character proof of concept.
- [PHASE3_PROGRESS.md](PHASE3_PROGRESS.md) records the body-model conversion and current verification status.
- Arrow-Forge's community ASBR CPK reader decoded `data/spc/2jsp01bod1.xfbin` from the supplied `data/launch/data.cpk` to a 3,076,423-byte `NUCC` XFBIN. This supersedes earlier failed generic decode attempts; no DRM/anti-cheat bypass or key recovery was used.
- Blender-XFBIN-Importer 2.5.2 in Blender 4.5.13 imported Jotaro as 7 mesh objects, 11,242 vertices, 16,598 faces, 182 bones, and 6 materials. Its exporter produced `1nrtbod1.xfbin`; re-import parsed 5 pages and preserved mesh, face, bone, and material counts (vertices +9).
- The local offline test payload is under `out/phase5/payload/`. SHA-256: `54B4CEC41AA38223A7EBABE4F9A5ED068E2A5012BE13F6F5C1A906F25C1AAF75`.
- At the user's request, the assistant copied only this new loose file to the supplied Storm 4 folder at `data_win32/spc/1nrtbod1.xfbin`; the destination did not exist beforehand. The install state records the file hash and the two directories created so the uninstaller can remove the override and empty directories. Existing CPK files were not modified.
- The user's first offline runtime test showed Naruto unchanged. The loose-file override did not produce a visible replacement; this does not identify whether the loader ignored it or rejected the candidate XFBIN. Runtime loading, textures, and animations remain unverified.
- Generated assets and downloaded tool sources stay local under `out/` and are excluded from Git.

## 2026-10-02 — Phase 4 animation investigation

- [PHASE4_PROGRESS.md](PHASE4_PROGRESS.md) records the Jotaro animation findings and verification limit.
- The ASBR motion XFBIN decodes to 246 pages and imports as 199 animation actions. Its 182-bone Jotaro rig has a name for every animation bone channel (no missing channel names in the report); this establishes compatibility with the ASBR Jotaro model only.
- The community animation exporter wrote a 957,588-byte XFBIN candidate. The installed XFBIN importer could not parse its animation chunk; the matching 1.0.6 add-on reader also rejected the file while parsing a model-group chunk. The candidate is not in the game payload.
- The Storm 4 Naruto body entry extracted from the archive does not start with `NUCC` and has not been decoded by the tools used. A Storm rig-to-Jotaro hierarchy/bind-pose comparison, a validated Storm animation override, moveset conversion, and voice/SFX conversion remain outstanding. No format or mapping has been guessed.

## 2026-10-02 — Phase 5 local installer and restore

- `out/phase5/Launch_Jotaro_Mod.bat` runs the PowerShell launcher, asks the user to confirm `OFFLINE`, installs the local `data_win32` payload with SHA-256 tracking, and starts `NSUNS4.exe` from the selected game folder. If the default game folder or payload is missing, it prompts for a replacement path.
- `out/phase5/Uninstall_Jotaro_Mod.bat` restores a saved original override or removes only the assistant-created file if its installed hash still matches. It leaves user-modified files untouched and reports conflicts.
- The loose-file method uses the supplied `data_win32` sample's path structure; Storm 4 runtime precedence is not verified. The launcher does not repack game archives and does not interact with DRM or anti-cheat.
- PowerShell syntax and mock install/uninstall flows passed: loose-file hash check; creation and cleanup of missing directories; restoration of an existing override from a verified backup; leaving a changed file untouched; and successful retry after the conflict is resolved. These tests used only disposable mock folders under `out/` and did not launch the actual game.
- Runtime test: user reported Naruto looked unchanged. Troubleshoot the loose-file/loader path and candidate validity before claiming a successful in-game port. This project’s scripts do not communicate with Steam.

