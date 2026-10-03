use sha2::{Digest, Sha256};
use std::path::{Path, PathBuf};

/// Absolute, normalized path (no symlink resolution needed for not-yet-existing outputs).
pub fn absolute(p: &Path) -> Result<PathBuf, String> {
    let base = if p.is_absolute() { PathBuf::new() } else { std::env::current_dir().map_err(|e| e.to_string())? };
    let mut out = PathBuf::new();
    for c in base.join(p).components() {
        match c {
            std::path::Component::ParentDir => {
                out.pop();
            }
            std::path::Component::CurDir => {}
            other => out.push(other),
        }
    }
    Ok(out)
}

/// Refuse any output path that is not inside `<project>/out/`.
pub fn guard_out(project: &Path, target: &Path) -> Result<PathBuf, String> {
    let out_root = absolute(&project.join("out"))?;
    let t = absolute(target)?;
    if t.starts_with(&out_root) && t != out_root {
        Ok(t)
    } else {
        Err(format!("refusing output outside {}: {}", out_root.display(), t.display()))
    }
}

/// Project root = nearest ancestor of `start` containing `mod/config`.
pub fn find_project(start: &Path) -> Result<PathBuf, String> {
    let mut cur = absolute(start)?;
    loop {
        if cur.join("mod").join("config").is_dir() {
            return Ok(cur);
        }
        if !cur.pop() {
            return Err("could not find project root (a folder containing mod/config)".into());
        }
    }
}

pub fn sha256_hex(data: &[u8]) -> String {
    Sha256::digest(data).iter().map(|b| format!("{b:02X}")).collect()
}

pub fn walk(dir: &Path, out: &mut Vec<PathBuf>) -> std::io::Result<()> {
    let mut entries: Vec<_> = std::fs::read_dir(dir)?.collect::<Result<_, _>>()?;
    entries.sort_by_key(|e| e.file_name());
    for e in entries {
        let p = e.path();
        if e.file_type()?.is_dir() {
            walk(&p, out)?;
        } else {
            out.push(p);
        }
    }
    Ok(())
}
