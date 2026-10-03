//! `stardust build`: assemble profile payloads from staged feature trees.
//!
//! Layout (all ignored by git):
//!   out/stardust/stage/<feature>/...   produced by the stage tools (ui, characters, ladder, ...)
//!   out/payload/<profile>/...          assembled payload + manifest.json + build_info.json
//!
//! A profile fails if no staged files exist for it, or two features stage the same path.

use crate::util;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashMap};
use std::path::{Path, PathBuf};

#[derive(Deserialize)]
pub struct Config {
    pub build: BuildInfo,
    #[serde(default)]
    pub features: HashMap<String, bool>,
    #[serde(default)]
    pub profiles: BTreeMap<String, Profile>,
    #[serde(default)]
    pub characters: Vec<toml::Value>,
    #[serde(default)]
    pub strings: Vec<StringEdit>,
}

#[derive(Deserialize)]
pub struct BuildInfo {
    pub name: String,
    pub version: String,
    pub stamp: String,
}

#[derive(Deserialize)]
pub struct Profile {
    pub include: Vec<String>,
}

#[derive(Deserialize)]
pub struct StringEdit {
    pub original: String,
    pub replacement: String,
    #[serde(default)]
    pub max_len: usize,
}

#[derive(Serialize)]
struct ManifestEntry {
    path: String,
    size: u64,
    sha256: String,
}

pub fn load_config(path: &Path) -> Result<(Config, String), String> {
    let raw = std::fs::read(path).map_err(|e| format!("{}: {e}", path.display()))?;
    let text = String::from_utf8(raw.clone()).map_err(|e| e.to_string())?;
    let cfg: Config = toml::from_str(&text).map_err(|e| format!("{}: {e}", path.display()))?;
    validate(&cfg)?;
    Ok((cfg, util::sha256_hex(&raw)))
}

fn validate(cfg: &Config) -> Result<(), String> {
    for s in &cfg.strings {
        let n = s.replacement.chars().count();
        if s.max_len > 0 && n > s.max_len {
            return Err(format!("string '{}' -> '{}' is {n} chars, table limit {}", s.original, s.replacement, s.max_len));
        }
    }
    for (name, p) in &cfg.profiles {
        if p.include.is_empty() {
            return Err(format!("profile {name} includes nothing"));
        }
    }
    Ok(())
}

/// Write `manifest.json` listing every file under `dir` (excluding the manifest itself).
pub fn write_manifest(dir: &Path) -> Result<usize, String> {
    let project = util::find_project(dir)?;
    let dir = util::guard_out(&project, dir)?;
    let mut files = vec![];
    util::walk(&dir, &mut files).map_err(|e| e.to_string())?;
    let mut entries = vec![];
    for f in files {
        let rel = f.strip_prefix(&dir).unwrap().to_string_lossy().replace('\\', "/");
        if rel == "manifest.json" {
            continue;
        }
        let data = std::fs::read(&f).map_err(|e| e.to_string())?;
        entries.push(ManifestEntry { path: rel, size: data.len() as u64, sha256: util::sha256_hex(&data) });
    }
    let n = entries.len();
    let json = serde_json::to_string_pretty(&entries).map_err(|e| e.to_string())?;
    std::fs::write(dir.join("manifest.json"), json).map_err(|e| e.to_string())?;
    Ok(n)
}

pub fn build_profile(project: &Path, cfg: &Config, cfg_hash: &str, name: &str) -> Result<usize, String> {
    let profile = cfg.profiles.get(name).ok_or_else(|| format!("unknown profile {name}"))?;
    let stage = project.join("out").join("stardust").join("stage");
    let dest = util::guard_out(project, &project.join("out").join("payload").join(name))?;
    if dest.exists() {
        std::fs::remove_dir_all(&dest).map_err(|e| e.to_string())?;
    }
    let mut owner: BTreeMap<String, String> = BTreeMap::new();
    let mut skipped = vec![];
    for feature in &profile.include {
        let src = stage.join(feature);
        if !src.is_dir() {
            skipped.push(feature.clone());
            continue;
        }
        let mut files = vec![];
        util::walk(&src, &mut files).map_err(|e| e.to_string())?;
        for f in files {
            let rel = f.strip_prefix(&src).unwrap().to_string_lossy().replace('\\', "/");
            if let Some(prev) = owner.insert(rel.clone(), feature.clone()) {
                return Err(format!("{rel} staged by both {prev} and {feature}"));
            }
            let to = dest.join(&rel);
            std::fs::create_dir_all(to.parent().unwrap()).map_err(|e| e.to_string())?;
            std::fs::copy(&f, &to).map_err(|e| format!("{}: {e}", f.display()))?;
        }
    }
    if owner.is_empty() {
        return Err(format!(
            "profile {name}: nothing staged under {} for {:?}; refusing to produce an empty payload",
            stage.display(),
            profile.include
        ));
    }
    let info = serde_json::json!({
        "name": cfg.build.name, "version": cfg.build.version, "stamp": cfg.build.stamp,
        "profile": name, "config_sha256": cfg_hash, "features_missing": skipped,
    });
    std::fs::write(dest.join("build_info.json"), serde_json::to_string_pretty(&info).unwrap()).map_err(|e| e.to_string())?;
    // Ladder-style profiles stage one sub-payload per rung (<RUNG>/data_win32/...):
    // give each its own manifest so the installer can install exactly one rung.
    let mut rungs = vec![];
    for e in std::fs::read_dir(&dest).map_err(|e| e.to_string())? {
        let p = e.map_err(|e| e.to_string())?.path();
        if p.join("data_win32").is_dir() {
            write_manifest(&p)?;
            rungs.push(p.file_name().unwrap().to_string_lossy().into_owned());
        }
    }
    rungs.sort();
    if !rungs.is_empty() {
        println!("profile {name}: per-rung manifests for {rungs:?}");
    }
    let n = write_manifest(&dest)?;
    println!("profile {name}: {n} files -> {}{}", dest.display(),
        if skipped.is_empty() { String::new() } else { format!(" (WARNING: nothing staged for {skipped:?})") });
    Ok(n)
}

pub fn run(args: &[String]) -> Result<(), String> {
    let (mut config, mut profile, mut project) = (None, None, None);
    let mut it = args.iter();
    while let Some(a) = it.next() {
        match a.as_str() {
            "--config" => config = it.next().map(PathBuf::from),
            "--profile" => profile = it.next().cloned(),
            "--project" => project = it.next().map(PathBuf::from),
            other => return Err(format!("unknown argument {other}")),
        }
    }
    let config = config.ok_or("--config required")?;
    let project = match project {
        Some(p) => util::absolute(&p)?,
        None => util::find_project(config.parent().unwrap_or(Path::new(".")))?,
    };
    let (cfg, hash) = load_config(&config)?;
    println!("config {} sha256={hash} stamp=\"{}\"", config.display(), cfg.build.stamp);
    let names: Vec<String> = match profile {
        Some(p) => vec![p],
        None => cfg.profiles.keys().cloned().collect(),
    };
    let mut failures = vec![];
    for n in &names {
        if let Err(e) = build_profile(&project, &cfg, &hash, n) {
            eprintln!("profile {n}: FAILED: {e}");
            failures.push(n.clone());
        }
    }
    if failures.is_empty() { Ok(()) } else { Err(format!("{} profile(s) failed: {failures:?}", failures.len())) }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn project() -> tempfile::TempDir {
        let d = tempfile::tempdir().unwrap();
        std::fs::create_dir_all(d.path().join("mod/config")).unwrap();
        std::fs::write(d.path().join("mod/config/s.toml"), r#"
[build]
name = "T"
version = "0.1"
stamp = "T v0.1"
[[strings]]
original = "Options"
replacement = "Stand"
max_len = 7
[profiles.a]
include = ["ui", "characters"]
[profiles.b]
include = ["ladder"]
"#).unwrap();
        d
    }

    #[test]
    fn builds_with_manifest_and_rejects_empty() {
        let d = project();
        let stage = d.path().join("out/stardust/stage/ui/data_win32/spc");
        std::fs::create_dir_all(&stage).unwrap();
        std::fs::write(stage.join("x.txt"), b"abc").unwrap();
        let (cfg, h) = load_config(&d.path().join("mod/config/s.toml")).unwrap();
        assert_eq!(build_profile(d.path(), &cfg, &h, "a").unwrap(), 2); // x.txt + build_info.json
        let m: serde_json::Value = serde_json::from_str(
            &std::fs::read_to_string(d.path().join("out/payload/a/manifest.json")).unwrap()).unwrap();
        let x = m.as_array().unwrap().iter().find(|e| e["path"] == "data_win32/spc/x.txt").unwrap();
        assert_eq!(x["sha256"], "BA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD");
        assert!(build_profile(d.path(), &cfg, &h, "b").unwrap_err().contains("nothing staged"));

        let rung = d.path().join("out/stardust/stage/ladder/L0/data_win32/spc");
        std::fs::create_dir_all(&rung).unwrap();
        std::fs::write(rung.join("1dio.txt"), b"d").unwrap();
        build_profile(d.path(), &cfg, &h, "b").unwrap();
        let m = std::fs::read_to_string(d.path().join("out/payload/b/L0/manifest.json")).unwrap();
        assert!(m.contains("\"data_win32/spc/1dio.txt\""));
    }

    #[test]
    fn rejects_overlong_string_and_collisions() {
        let d = project();
        let p = d.path().join("mod/config/s.toml");
        let t = std::fs::read_to_string(&p).unwrap().replace("\"Stand\"", "\"Stand Settings\"");
        std::fs::write(&p, t).unwrap();
        assert!(load_config(&p).err().unwrap().contains("table limit 7"));

        let d = project();
        for f in ["ui", "characters"] {
            let s = d.path().join("out/stardust/stage").join(f);
            std::fs::create_dir_all(&s).unwrap();
            std::fs::write(s.join("same.txt"), f).unwrap();
        }
        let (cfg, h) = load_config(&d.path().join("mod/config/s.toml")).unwrap();
        assert!(build_profile(d.path(), &cfg, &h, "a").unwrap_err().contains("staged by both"));
    }

    #[test]
    fn output_guard_blocks_escape() {
        let d = project();
        assert!(util::guard_out(d.path(), &d.path().join("out/../evil")).is_err());
        assert!(util::guard_out(d.path(), &d.path().join("out")).is_err());
        assert!(util::guard_out(d.path(), &d.path().join("out/payload/x")).is_ok());
    }
}
