//! Scan a directory for strings in several encodings and log every hit.

use crate::util;
use encoding_rs::SHIFT_JIS;
use std::fmt::Write as _;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, PartialEq)]
pub struct Hit {
    pub file: PathBuf,
    pub offset: usize,
    pub encoding: &'static str,
    pub needle: String,
}

/// Note: UTF-16LE text preceded by a 0x00 byte also matches the UTF-16BE pattern one
/// byte earlier. Such paired hits are one string; trust the even-aligned LE hit.
///
/// Byte patterns for `s` in each supported encoding. Shift-JIS is skipped when it
/// would equal the UTF-8 bytes (pure ASCII), so a hit is reported once per encoding.
pub fn patterns(s: &str) -> Vec<(&'static str, Vec<u8>)> {
    let mut v = vec![("utf-8", s.as_bytes().to_vec())];
    v.push(("utf-16le", s.encode_utf16().flat_map(u16::to_le_bytes).collect()));
    v.push(("utf-16be", s.encode_utf16().flat_map(u16::to_be_bytes).collect()));
    let (sjis, _, unmappable) = SHIFT_JIS.encode(s);
    if !unmappable && sjis.as_ref() != s.as_bytes() {
        v.push(("shift-jis", sjis.into_owned()));
    }
    v
}

fn find_all(hay: &[u8], needle: &[u8]) -> Vec<usize> {
    if needle.is_empty() || needle.len() > hay.len() {
        return vec![];
    }
    hay.windows(needle.len()).enumerate().filter(|(_, w)| *w == needle).map(|(i, _)| i).collect()
}

pub fn scan(dir: &Path, needles: &[String]) -> Result<Vec<Hit>, String> {
    let mut files = vec![];
    util::walk(dir, &mut files).map_err(|e| format!("{}: {e}", dir.display()))?;
    let pats: Vec<_> = needles.iter().map(|n| (n.clone(), patterns(n))).collect();
    let mut hits = vec![];
    for f in files {
        let data = std::fs::read(&f).map_err(|e| format!("{}: {e}", f.display()))?;
        for (needle, ps) in &pats {
            for (enc, bytes) in ps {
                for off in find_all(&data, bytes) {
                    hits.push(Hit { file: f.clone(), offset: off, encoding: enc, needle: needle.clone() });
                }
            }
        }
    }
    Ok(hits)
}

pub fn run(args: &[String]) -> Result<(), String> {
    let (mut dir, mut out, mut needles) = (None, None, vec![]);
    let mut it = args.iter();
    while let Some(a) = it.next() {
        match a.as_str() {
            "--dir" => dir = it.next().cloned(),
            "--out" => out = it.next().cloned(),
            _ => needles.push(a.clone()),
        }
    }
    let (dir, out) = (dir.ok_or("--dir required")?, out.ok_or("--out required")?);
    if needles.is_empty() {
        return Err("give at least one string".into());
    }
    let project = util::find_project(Path::new("."))?;
    let out = util::guard_out(&project, Path::new(&out))?;
    let hits = scan(Path::new(&dir), &needles)?;
    let mut tsv = String::from("file\toffset\tencoding\tstring\n");
    for h in &hits {
        let _ = writeln!(tsv, "{}\t0x{:X}\t{}\t{}", h.file.display(), h.offset, h.encoding, h.needle);
    }
    if let Some(p) = out.parent() {
        std::fs::create_dir_all(p).map_err(|e| e.to_string())?;
    }
    std::fs::write(&out, &tsv).map_err(|e| e.to_string())?;
    println!("{} hits written to {}", hits.len(), out.display());
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn finds_planted_strings_in_all_encodings() {
        let d = tempfile::tempdir().unwrap();
        let mut blob = b"junk\x00".to_vec();
        blob.extend(b"Free Battle");
        blob.extend(b"..."); // non-zero gap: a 0x00 before UTF-16LE text also matches UTF-16BE at offset-1
        blob.extend("Free Battle".encode_utf16().flat_map(u16::to_le_bytes));
        blob.extend("Free Battle".encode_utf16().flat_map(u16::to_be_bytes));
        blob.push(b'!');
        let (sj, _, _) = SHIFT_JIS.encode("承太郎");
        blob.extend(sj.iter());
        std::fs::create_dir(d.path().join("sub")).unwrap();
        std::fs::write(d.path().join("sub/planted.bin"), &blob).unwrap();
        let hits = scan(d.path(), &["Free Battle".into(), "承太郎".into()]).unwrap();
        let encs: Vec<_> = hits.iter().map(|h| (h.encoding, h.offset)).collect();
        assert!(encs.contains(&("utf-8", 5)));
        assert!(encs.contains(&("utf-16le", 19)));
        assert!(encs.contains(&("utf-16be", 41)));
        assert!(encs.iter().any(|(e, o)| *e == "shift-jis" && *o == 64));
        assert_eq!(hits.len(), 4);
    }
}
