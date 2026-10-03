# FOUNDATION_REPORT — why didn't Naruto change? (Goal 0)

Status: **analysis from repo evidence only; no new runtime or file evidence.** This run had no access to the game installs, dio_port, the extracted catalogs, or the community tools (see DECISIONS.md). Every cause below is still a HYPOTHESIS. The ranking is by how well it fits the evidence we have, and by how cheaply it can be tested.

## What we know (from PHASE1–5, NOTES)

- The candidate is a valid-looking NUCC file. Our reader re-parses it (5 pages, 182 bones). Storm 4 acceptance has never been shown.
- It was installed as a **new** file `data_win32/spc/1nrtbod1.xfbin`. The launcher used the game root as working directory. Naruto looked unchanged; no crash was reported.
- Inside the CPKs, entries are addressed as `data/...` (ASBR `data/spc/2jsp01bod1.xfbin`). The Storm 4 entry path for Naruto's body was **never written down**. The `data_win32/` prefix comes from the dio_port sample's folder layout, not from a documented Storm 4 loose-file rule.
- dio_port contains `spc/` *and* `spcload/` files plus a `prm` file (`1tmrprm.bin.xfbin`). The Jotaro payload has only a body.
- The vanilla Storm Naruto body extracted by CPK Tool is the *stored* (compressed) payload, so no comparison has been possible.

## Ranked causes

| Rank | Cause | Evidence for | Evidence against | Settled by |
|---|---|---|---|---|
| 1 | **C1 — the game never reads loose files at `data_win32/spc/`.** Variant to keep in mind: `data_win32/` may be the *input folder for a CPK repack / Modding-API workflow*, not a folder the stock exe scans. | No change at all and no crash, which fits "file never opened". Phase 1 lists the Modding API (custom CPK loading) as the documented route. CPK-internal paths use `data/`, not `data_win32/`. | dio_port ships as a `data_win32` tree, which suggests some workflow uses it as-is. | **L0 + ProcMon** (one session). No ProcMon rows for `data_win32` means C1. |
| 2 | **C3 — the file is read but rejected or ignored** (ASBR-flavoured materials/shaders, chunk layout, NUCC version, clump/bone names). | It is an ASBR export with ASBR materials, and the exporter changed the vertex count by +9. Storm's structure was never compared (B1 blocked). | Silent fallback without a crash is less typical than a crash for a malformed model, but CC2 games are known to fall back. | ProcMon `SUCCESS` on the open, then **L1** (Storm-native round trip). If L1 shows and Jotaro doesn't: C3. |
| 3 | **C2 — the slot needs more than the body** (spcload preload list, prm/param file, companion files). | dio_port carries `spcload/` and a `prm` file; Jotaro carries neither. | A body-only *replacement* under an existing name normally needs no new param data. That rule only matters for **new** names (B3 Q1). | B3 Q1/Q2 (dio_port anatomy) + L0. |
| 4 | **C4 — the tested costume/form doesn't use `1nrtbod1`.** | Storm 4 has many Naruto variants (Sage, Kurama, Hokage, ...), each with its own code. `NARUTO_COSTUME_TESTED` was never recorded. | `1nrt` is the base Naruto prefix in the CPK catalog (Phase 3). | ProcMon bonus capture (`Path contains 1nrt`) shows which files the chosen Naruto loads. |

## Recommended first test

One session: **install L0 (dio_port as-is) with the new installer, run ProcMon per `docs/procmon_howto.md` (including the `1nrt` bonus capture), and fill in `RUNTIME_RESULTS.md`.** That separates C1 from C2/C3, and the bonus capture covers C4.

## Unknowns stated plainly

- The Storm 4 CPK entry path and the decoded bytes for Naruto's body (B1 not run here).
- Whether dio_port is meant to be loaded loose, through the Modding API, or repacked (B3 not run here).
- Which slot `1tmr` is (B3 Q3).
