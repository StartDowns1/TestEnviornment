# Phase 1 — Recon findings

Date: 2026-10-02  
Scope: read-only inventory and signature inspection. No game files were changed, extracted, repacked, or launched.

## Verdict

**Promising for a replacement-character proof of concept; not yet demonstrated in-game.** Both installs contain CRI `.cpk` archives and CyberConnect2 `NUCC`/XFBIN files. Community tooling documents loose `data_win32` replacements for Storm 4, and an optional Storm 4 modding API can load prioritized custom CPKs. Prefer a staged loose-file payload for the first test: it avoids rebuilding large base archives. The game folder was explicitly treated as read-only, so any later installer must stage into `out` and require the user to apply it themselves (or create a separate game copy).

Cross-game XFBIN/NUCC familiarity is useful, but does **not** mean model, rig, animation, move, or audio payloads are interchangeable. A character becomes playable only if Storm 4 accepts its asset graph and its own character/slot parameters.

## Inventory (observed locally)

| Tree | Files | Bytes | Relevant observed contents |
|---|---:|---:|---|
| `Downloads/dio_port/data_win32` | 31 | 63,829,278 | 30 `.xfbin` plus a `.bak`; `spc` and `spcload` paths, including `1dio...` XFBINs and `1tmrprm.bin.xfbin` |
| ASBR root | 131 | 5,323,313,991 | 36 `.cpk`, 5 loose `.xfbin`, executable and support files |
| Storm 4 root | 1,025 | 41,797,629,853 | 29 `.cpk`, 9 loose `.xfbin`, 825 `.gfx` and support files; includes `data/disc/movie2.cpk` and `movie3.cpk` larger than 2 GB each |

ASBR archive paths include `data/launch/data.cpk`, `platform.cpk`, `sound.cpk`, `stage.cpk`, locale CPKs, and numbered `data/patch/patch*.cpk` files. Storm 4 includes `data/launch/data1.cpk`, `stage1.cpk`, `sound.cpk`, locale `dataRegion.cpk` files, `data/patch/12/{data,launch,sound}.cpk`, `data/sim/{data2,stage2}.cpk`, DLC CPKs, and very large movie CPKs. Storm system files include e.g. `data/system/content_info.xfbin` and `ccAdjustParam*.xfbin`.

The supplied `dio_port/data_win32` is a pre-existing mod payload, not either game’s install tree. Its names and folders match known Storm 4 mod conventions and provide a concrete character-related sample, but its contents were not parsed or tested.

## Formats, compression, encryption

- **CPK:** Sample archive headers begin with ASCII `CPK ` and include the recognizable CRI UTF-table marker. This identifies a CRI CPK container. Header inspection alone does not establish per-entry compression, CRILAYLA use, integrity, or whether any embedded asset payload is encrypted. Those require listing archive metadata and examining entries with a known tool during Phase 2.
- **XFBIN:** Inspected loose XFBINs begin with `NUCC` followed by a version-like header field. The Storm 4 `content_info.xfbin` contains readable chunk labels such as `nuccChunkBinary`, `nuccChunkPage`, and `nuccChunkIndex`. This is strong evidence of the CC2 NUCC/XFBIN family and no outer-file encryption on these samples; it does not prove every nested chunk is uncompressed or understood.
- **Audio:** Both installs have `adx2.cpk` and `sound.cpk`; their actual entries/codecs/keys were not enumerated. Do not assume audio payloads or event maps transfer between games.
- **Encryption status:** No encrypted header was observed in the sampled CPK/XFBIN files. No claim is made about individual compressed or encrypted archive entries.

## Storm 4 override/loading approach

Storm 4’s community modding documentation and long-running mod examples describe a root-level `data_win32` tree containing replacement paths such as `spc`/`spcload`. A separate Storm 4 Modding API documents loading new CPKs at configurable priority without replacing base CPKs. Therefore the supported candidate approaches are:

1. **Loose `data_win32` overrides (preferred first):** common, small, and reversible by removing only the installed mod files. Community evidence is strong; not runtime-tested against this supplied Storm install.
2. **Mod API custom CPK:** documented priority override and suited to bundling many files, but needs a loader/API installed beside the game. It is an optional runtime dependency and requires user-side installation. Do not replace the game’s original CPKs.

At the time of Phase 1, no install was attempted. Later, after explicit user authorization, a generated loose model file was copied into the supplied Storm folder and recorded for restoration; see the Phase 3 and Phase 5 reports. The original CPK archives were not modified.

## Asset feasibility

| Asset | Feasibility | Basis and remaining proof |
|---|---|---|
| Models / meshes | **Medium** | Both use NUCC/XFBIN; the `nuccbin-asbr` and Storm tooling ecosystems parse related structures. Need compare actual model chunks, vertex formats, material references, and test one converted replacement in Storm. A format-family match is not binary compatibility. |
| Textures | **Medium-high** | Textures are commonly embedded in CC2 XFBIN/NUCC chunks; community tools include Storm texture editors and ASBR StoneMask/NUT workflows. Need compare texture chunk formats, swizzles, mipmaps, and material bindings. |
| Skeleton / rig | **Low-medium** | Potentially representable in related chunks, but the rigs, bone names/order, bind pose, scale, and expected dummy bones may differ. Must inspect source and target character skeletons and document a mapping before asserting conversion. |
| Animations | **Low** | Likely CC2 animation data, but target bone tracks, animation state naming, timing, effects, and runtime conditions are game-specific. Requires parsing plus retargeting and in-game movement checks. |
| Moveset / character logic | **Low** | Storm 4 uses its own PRM/skill/character parameter systems and may have hardcoded behaviors. ASBR moves cannot be copied as-is; first define what a “port” means (slot replacement vs new selectable character) and map to Storm attacks/specials. |
| Voice / SFX | **Low-medium** | Shared CC2 ecosystem and community notes report XFBIN-based sound work, but these installs’ audio payloads, banks, event bindings, sample rates, and metadata were not inspected. Reuse may be possible after audio conversion and Storm event remapping. |

**Practical scope:** Start with a Storm 4 slot replacement using a static model and textures. That is much more feasible than creating a new selectable character or transferring ASBR logic. Then add a compatible Storm animation set, and treat audio/moves as separate later milestones.

## Existing tools and references

- [Storm 4 Modding API](https://github.com/zealottormunds/ns4moddingapi) — documents prioritized custom CPK loading and patch/plugin support.
- [NSUNS4 Toolbox releases](https://github.com/TheLeonX/NSUNS4-Toolbox/releases) — Storm character, parameter, animation, and XFBIN-adjacent workflows; use before implementing equivalent editors.
- [Storm 4 / Connections Toolbox source](https://github.com/TheLeonX/NSC-Toolbox) — documents a combined toolbox and supported parameter formats.
- [ASBR modding guide](https://jojowiki.com/index.php?mobileaction=toggle_view_mobile&title=User%3AKojoB%2FASBR_Modding) — documents ASBR `data_win32` loose XFBIN override paths and CPK workflow.
- [CriPakTools](https://github.com/wmltogether/CriPakTools) — community CPK reader/extractor/repacker referenced by Storm/ASBR modding guides. Evaluate in Phase 2; do not repack any original archive.
- [StoneMask](https://github.com/Vishkujo/StoneMask/releases) — ASBR XFBIN texture inspection/replacement tool for texture-bearing files.
- [nuccbin-asbr](https://github.com/JoJosBizarreModdingCommunity/nuccbin-asbr) — ASBR NUCC chunk binary serializer/deserializer; useful reference for ASBR chunks, not a proven Storm converter.
- [xfbin_lib](https://github.com/mosamadeeb/xfbin_lib) — Python reference implementation for CC2 XFBIN/NUCC structures; inspect for format notes before writing Rust parsers.
- [Noesis](https://richwhitehouse.com/index.php?content=inc_projects.php) and community CC2 plugins may help view/export meshes and textures, but compatibility with these exact builds remains to be checked.

## Verification and limits

- Verified locally: recursive path/extension/size inventories; sample CPK and XFBIN signatures; readable NUCC chunk labels in the Storm system XFBIN.
- Not verified: archive listing/extraction, per-entry compression/encryption, round-trip packing, model/texture import, Storm runtime loose-file precedence, character select, animation playback, audio playback, or offline-only behavior.
- The user stated they own both games. The supplied game folders were used as local inputs; no Steam client was accessed or contacted. No DRM, anti-cheat, or online features were used. Runtime results describe only the supplied Storm folder.

## Phase 1 decision

**Proceed to Phase 2 only after the user reviews these findings.** Phase 2 should first implement an inventory/listing reader and use existing community CPK/XFBIN tools as validation references; no full archive extraction or repacking is necessary merely to enumerate entries. Keep generated/extracted content local under ignored `out` paths and never commit game assets.

