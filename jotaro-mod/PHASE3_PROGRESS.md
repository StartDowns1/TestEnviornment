# Phase 3 — Jotaro body proof of concept

Date: 2026-10-02

## Status

**First offline in-game test failed: Naruto looked unchanged.** A Jotaro body XFBIN was decoded, imported, renamed/exported for the Naruto slot, and successfully re-imported by the Blender XFBIN add-on. The body is installed as a new loose file at `data_win32/spc/1nrtbod1.xfbin`; its hash matches the local payload. The unchanged result means the runtime override and/or exported asset has not been validated; this is not yet a successful in-game proof of concept.

## Source and tools

- Jotaro's ASBR character code is `2jsp01`. The source body is `data/spc/2jsp01bod1.xfbin` from the supplied base `data/launch/data.cpk`.
- `out/phase3-work/extract_asbr_asset.py` uses the community [Arrow-Forge](https://github.com/ImGoldenWind/Arrow-Forge) CPK reader to decode the entry. The decoded body is 3,076,423 bytes and starts with `NUCC`.
- The model was parsed and exported with [Blender-XFBIN-Importer](https://github.com/Al-Hydra/Blender-XFBIN-Importer) 2.5.2 in Blender 4.5.13. Source scripts and all generated/intermediate files remain under ignored `out/phase3-work/`.
- A Storm 4 loose-file character mod sample supplied by the user has `data_win32/spc` and `data_win32/spcload` paths. Phase 1 also cites the community [Storm 4 Modding API](https://github.com/zealottormunds/ns4moddingapi), which supports prioritized custom CPK loading. Neither loader method has been runtime-tested here; the first candidate follows the loose-file sample path.

## Conversion performed

- Imported source scene: 7 mesh objects, 11,242 vertices, 16,598 faces, one 182-bone armature, and 6 materials.
- Exported `1nrtbod1.xfbin` from the Jotaro body collection with mesh, bones, dynamics, and embedded textures. The exporter renamed the `2jsp01` content prefix to `1nrt` for the Naruto target slot.
- Re-imported the export successfully: 5 XFBIN pages; 7 mesh objects; 11,251 vertices; 16,598 faces; one 182-bone armature; 6 renamed materials. The +9 vertex count is recorded as an exporter change; the face count and bone count were preserved.
- The candidate's first four bytes are `NUCC`. Size is 2,626,587 bytes and SHA-256 is `54B4CEC41AA38223A7EBABE4F9A5ED068E2A5012BE13F6F5C1A906F25C1AAF75`.
- The local test payload is `out/phase5/payload/data_win32/spc/1nrtbod1.xfbin`; [PHASE5_README.md](PHASE5_README.md) documents the launcher and restore step. The file was copied to the supplied Storm 4 folder as a new loose override after confirming that the target file did not previously exist. No original game archive or other game file was changed.

## Skeleton / asset limits

The source and exported model each have 182 bones. The export renames the model's prefix, but the exact Storm Naruto rig hierarchy/bind pose has not been compared against a decoded target asset, and no animation tracks have been retargeted. Accessories, attacks, special moves, voice, and SFX are not included. Material images are embedded in the XFBIN, but only structural/material-name survival was checked; no in-game texture appearance has been verified.

## Verification

- **Verified:** community parser decoded the exact supplied Jotaro body entry to `NUCC`; Blender imported the source; the XFBIN exporter wrote a Naruto-slot candidate; Blender's XFBIN reader re-parsed it; re-import preserved mesh count, face count, bone count, and material count; local payload and installed loose-file hashes match.
- **Observed failure:** the user's offline run showed Naruto unchanged.
- **Still unverified:** whether this supplied Storm 4 build reads the loose override; whether the candidate is accepted/rendered; textures; rig behavior under Storm animations; offline battle stability. The unchanged result alone does not distinguish a path/loader issue from a rejected or incompatible XFBIN.
- The next useful step is to verify the supplied build's asset override mechanism and inspect runtime logs before treating any generated model as loaded.

## References

- [Arrow-Forge](https://github.com/ImGoldenWind/Arrow-Forge) — community ASBR archive/payload reader used for extraction.
- [Blender-XFBIN-Importer](https://github.com/Al-Hydra/Blender-XFBIN-Importer) — community XFBIN importer/exporter used for parsing and conversion.
- [Storm 4 Modding API](https://github.com/zealottormunds/ns4moddingapi) — custom CPK loading option identified during Phase 1; not needed for this staged test.
- [ASBR modding guide](https://jojowiki.com/index.php?mobileaction=toggle_view_mobile&title=User%3AKojoB%2FASBR_Modding) — community reference for CC2 loose-file/CPK modding workflow.

