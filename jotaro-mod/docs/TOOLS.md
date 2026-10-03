# Tools register

| Tool | Source | Version | SHA-256 | Use |
|---|---|---|---|---|
| PowerShell (Linux x64) | https://github.com/PowerShell/PowerShell/releases/download/v7.4.6/powershell-7.4.6-linux-x64.tar.gz | 7.4.6 | `6F6015203C47806C5CC444C19D8ED019695E610FBD948154264BF9CA8E157561` | Cloud-session only: running `installer/test_installer.ps1` against mock folders. Not stored in the repo. |
| Rust crates (crates.io) | `encoding_rs 0.8`, `serde 1`, `serde_json 1`, `sha2 0.10`, `toml 0.8`, `tempfile 3` (dev) | pinned in `tools/stardust-tools/Cargo.lock` | lockfile checksums | `stardust-tools` |

Earlier local tools (CPK Tool 1.1.0, Arrow-Forge, Blender-XFBIN-Importer 2.5.2, cc2_anm_export_blender 1.0.5) are documented in PHASE2/3/4. Their exact release hashes were never recorded. **TODO for the user's PC:** run `Get-FileHash` on `out\tools\*` and add rows here.
