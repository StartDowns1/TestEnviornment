//! `stardust` — offline build helpers for the Stardust Storm mod.
//!
//! Every write is confined to the project's `out/` tree. Nothing here reads or
//! writes a game folder; the installer in `installer/` does that, run by the user.

#[allow(dead_code)]
mod build;
mod findstr;
mod magic;
mod util;

use std::path::PathBuf;
use std::process::ExitCode;

const USAGE: &str = "usage:
  stardust findstr --dir <scan-dir> --out <log under out/> <string>...
  stardust magic <file>...
  stardust build --config <stardust.toml> [--profile <name>] [--project <root>]
  stardust manifest <dir under out/>";

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let result = match args.first().map(String::as_str) {
        Some("findstr") => findstr::run(&args[1..]),
        Some("magic") => magic::run(&args[1..]),
        Some("build") => build::run(&args[1..]),
        Some("manifest") => args
            .get(1)
            .ok_or_else(|| USAGE.to_string())
            .and_then(|d| build::write_manifest(&PathBuf::from(d)).map(|n| println!("manifest: {n} files"))),
        _ => Err(USAGE.to_string()),
    };
    match result {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("error: {e}");
            ExitCode::FAILURE
        }
    }
}
