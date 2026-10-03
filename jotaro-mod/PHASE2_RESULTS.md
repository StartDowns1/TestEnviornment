# Phase 2 — Reader/extractor results

Date: 2026-10-02

## Delivered

- Rust CLI source in [`out/rust/src/main.rs`](out/rust/src/main.rs), with commands to list a CPK, extract into `out/`, round-trip an archive, and catalog a game tree.
- The CLI checks CPK magic, restricts generated output to the project `out/` folder, validates archive entry paths before extraction, and never writes to game archives.
- CPK parsing, stored-entry extraction, and CPK rebuilding are delegated to the existing [CPK Tool](https://github.com/darkruss48/cpk-toolkit), rather than duplicated. Its executable is locally stored at `out/tools/cpk-tool.exe` and ignored by Git; the tool is not vendored.
- Build and dependency instructions are in [`out/rust/README.md`](out/rust/README.md).

## Verification

- `cargo check` succeeded; optimized Windows CLI build succeeded using Rust stable and LLVM-MinGW.
- The compiled CLI listed the ASBR main `data.cpk` (3,642 entries) and Storm 4 `data1.cpk` (5,190 entries).
- Full catalogs completed for both supplied game trees with zero CPK listing failures: ASBR 36 CPK + 5 loose XFBIN; Storm 4 29 CPK + 9 loose XFBIN. Full listings are available locally under ignored `out/phase2-work/`.
- The CLI output-path guard was exercised: an extraction request targeting outside `out/` failed, and the requested outside path was not created.
- CPK extraction followed by packing the extracted directory produced byte-identical archives:

| Archive | Extracted entries | Size | SHA-256 (source and rebuilt) |
|---|---:|---:|---|
| ASBR `data/patch/patch120.cpk` | 34 | 248,676 B | `4c92962dbcddbaaa4a3630dc5d2001a11c21a573ea24de367fb5f7d103e62531` |
| Storm 4 `dlc/5/data/sim/data.cpk` | 37 | 56,617,862 B | `9e281fbb9cc65b2f54d594af16210b3da74eeb7d4c99fa93210391d3a4f36d7f` |
| Storm 4 `dlc/10/data/sim/data.cpk` | 2 | 6,468 B | `73739b48b50cecb3863cca4d86ce5fde453ee538900c064780b4bfede613df3b` |

No source archive was modified.

## Format findings and limits

- **Correction from Phase 3 asset probing:** CPK Tool extraction preserves the stored entry payload for files marked compressed; it does not provide decoded game-facing bytes for those entries. For example, ASBR `patch120.cpk` lists `data/skill/3hhs01_x.xfbin` as 183.59 KB with a 12.45 KB stored payload, and both full-archive and single-file extraction produced 12,752 bytes. Thus extraction and exact repacking validate CPK entry preservation, not payload decompression or loadability.
- The Rust CLI does not decode or decrypt inner XFBIN payloads. Phase 2 is complete at the CPK listing, stored-entry extraction, and exact-round-trip layer; game-facing asset decoding remains outstanding.
- A sampled Storm 4 extracted XFBIN begins with `NUCC`. ASBR patch120 entries `data/spc/3dio01prm.bin.xfbin` and `data/skill/7dio01_x.xfbin` begin with `54-09-41-02` and `23-FB-57-04`, respectively, rather than `NUCC`. Their inner encoding or encryption has not been identified, and no decoding attempt was made. CPK round-trip success does not establish that all ASBR assets are directly readable or reusable.
- No game was launched, no in-game load test was made, and no gameplay, animation, or audio was verified. The supplied game folders remained read-only.
- No game assets are part of the tracked project. Extracted files, catalogs, CPK utility, compiler/linker downloads, and compiled CLI remain ignored local output under `out/`.

## Phase decision

Phase 2 is complete for CPK listing, stored-entry extraction, and exact round-trip validation. It did not decode compressed/encrypted entry payloads into game-facing XFBIN files. Treat non-`NUCC` signatures in those stored streams as unresolved until the required game-specific transform is verified.

