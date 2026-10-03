# CC2 Asset CLI

Small Rust front end for listing and extracting stored entries from CRI CPK archives from Storm 4 and ASBR. It delegates CPK parsing and rebuilding to the community [CPK Tool](https://github.com/darkruss48/cpk-toolkit), rather than duplicating that code. Entries marked compressed may remain in stored compressed/encrypted form after extraction; this CLI does not decode game-facing XFBIN contents.

## Dependency setup

Download the Windows release `cpk-tool.exe` from the linked project and place it at `out/tools/cpk-tool.exe` (or pass `--tool <path>`). The executable is ignored by Git. The locally inspected release is v1.1.0, SHA-256 `F9EB21D9B74994B12910DE6B5F0982711EEF7CF4B76850516B6757A6A9F7A545`.

## Build

From the project root, with Rust stable and a Windows linker installed:

```powershell
$env:CARGO_TARGET_X86_64_PC_WINDOWS_GNU_LINKER = "<llvm-mingw>\bin\x86_64-w64-mingw32-clang.exe"
$env:CARGO_TARGET_DIR = (Resolve-Path .\out).Path + "\rust\target"
cargo build --manifest-path .\out\rust\Cargo.toml --release --target x86_64-pc-windows-gnu
```

The tested workspace used Rust stable and LLVM-MinGW's MSVCRT x86-64 target. A standard MSVC build can instead run from a Visual Studio Developer PowerShell with its linker available.

## Commands

```text
cc2-asset-cli list <archive.cpk> [--tool <cpk-tool.exe>]
cc2-asset-cli extract <archive.cpk> <out-directory> [--tool <cpk-tool.exe>]
cc2-asset-cli roundtrip <archive.cpk> <out-work-directory> [--tool <cpk-tool.exe>]
cc2-asset-cli catalog <game-root> <out-report.txt> [--tool <cpk-tool.exe>]
```

All extraction, round-trip, and catalog outputs are required to live under this project's `out/` directory. `catalog` inventories loose XFBINs and asks CPK Tool to list every CPK under a supplied game root. `roundtrip` extracts an archive, packs the extracted directory, then compares the rebuilt archive byte-for-byte with the original. It never writes to an input archive.

This front end does not unpack XFBIN chunks. Phase 2 validates archive transport and inventory; XFBIN parsing is a later tool layer.

## References

- [CPK Tool source and CLI documentation](https://github.com/darkruss48/cpk-toolkit)
- [LLVM-MinGW releases](https://github.com/mstorsjo/llvm-mingw/releases)
- [Rust installation](https://www.rust-lang.org/tools/install)

