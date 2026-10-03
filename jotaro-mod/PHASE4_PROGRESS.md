# Phase 4 — Jotaro animations, moveset, voice, and SFX

Date: 2026-10-02

## Status

**Animation source analysis is complete; a verified Storm 4 animation replacement is not.** I did not install the exported motion candidate. Phase 4 needs a working offline game check plus a readable Storm target rig/animation mapping before a Jotaro motion XFBIN can be treated as safe.

## What was inspected

- ASBR Jotaro is character code `2jsp01`. The character motion file is `2jsp01mot1.xfbin`; its decoded XFBIN has 246 pages. The companion `2jsp01_anmofs.xfbin` has 86 pages and holds animation references/offset information.
- Blender-XFBIN-Importer 2.5.2 imported the motion file with Jotaro's 182-bone model. It created 199 actions, 246,005 f-curves, and 2,011,665 keyframes. 240,999 f-curves target the Jotaro armature. Every bone channel name matched one of the source Jotaro rig's 182 names; none were missing.
- Community exporter [`cc2_anm_export_blender`](https://github.com/maxcabd/cc2_anm_export_blender) 1.0.5 wrote a 957,588-byte animation XFBIN. SHA-256: `CDF7890D459BC65768C05C9F5E4EC96EAAB63D092617EFD4E08E396D7C941C16`.

## Validation and limit

- **Tested:** Imported source body and motion into Blender; inspected animation actions and rig-channel names. Ran the exporter and attempted to read the resulting XFBIN using both the model add-on reader and the matching base add-on 1.0.6. The first reader stops in `NuccChunkAnm` while reading its entry count. The second stops in a model-group chunk. These independent failures mean the exported file has not passed structural validation. The exporter itself reporting “Finished exporting” is not enough to call it valid.
- **Not tested:** Storm 4 loading of any animation file, in-game character animation, attack behavior, timing, effects, or multiplayer/offline stability.
- The motion candidate remains only in ignored local analysis output at `out/phase4-work/jotaro_motion_reexport.xfbin`; it is not in the launcher payload or the game folder.

The extracted Storm 4 Naruto body entry at `out/phase3-work/storm-naruto/spc/1nrtbod1.xfbin` does not begin with `NUCC` and was not accepted by the available XFBIN reader. Its on-disk transform and the Storm skeleton hierarchy/bind pose are unknown. I have not guessed a key, decoder, bone mapping, or file layout. A Jotaro rig matching its own ASBR animation channels does not prove that Storm 4 accepts the same animation structures.

## Moveset, voice, and sound effects

No moveset, voice, or SFX override is included. The `2jsp01_anmofs.xfbin` references and Storm 4 character offsets have not been validated against the game. Movesets require confirmed Storm 4 slot data and attack/animation references; audio needs a verified Storm-compatible bank/stream mapping. Converting or assigning these without the first runtime test and a readable target format would be speculative.

## Phase decision

Keep the body-only model test as the current playable check point. Wait for the user to report the offline test result before replacing additional `1nrt` assets. If the body loads, the next technical gate is decoding and comparing the Storm 4 Naruto model/offset structures with the ASBR rig and validating one animation XFBIN in-game. If it does not load, first fix the loader/path or model compatibility.

## Tools and references

- [Blender-XFBIN-Importer](https://github.com/Al-Hydra/Blender-XFBIN-Importer) — model/motion import and body export.
- [cc2_anm_export_blender](https://github.com/maxcabd/cc2_anm_export_blender) — community Storm/ASBR animation exporter; its output did not pass our parsers in this attempt.
- [cc2_xfbin_blender_anm](https://github.com/maxcabd/cc2_xfbin_blender_anm) — matching base add-on 1.0.6; its reader was also tried as a validator.
- Generated reports and scratch exports are local-only under ignored `out/phase3-work/` and `out/phase4-work/`.

