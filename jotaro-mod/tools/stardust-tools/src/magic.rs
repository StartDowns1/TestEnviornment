//! Identify wrappers by magic bytes (prompt Appendix A). Unknown → hex + entropy, no guessing.

pub fn identify(head: &[u8]) -> &'static str {
    let starts = |m: &[u8]| head.starts_with(m);
    if starts(b"NUCC") {
        "XFBIN (NUCC)"
    } else if starts(b"CPK ") {
        "CRI CPK archive"
    } else if starts(b"CRILAYLA") {
        "CRILAYLA compressed"
    } else if starts(b"DDS ") {
        "DDS texture"
    } else if starts(b"FWS") || starts(b"CWS") || starts(b"ZWS") {
        "Flash SWF"
    } else if starts(b"GFX") || starts(b"CFX") {
        "Scaleform GFX"
    } else if starts(&[0x28, 0xB5, 0x2F, 0xFD]) {
        "zstd"
    } else if starts(&[0x04, 0x22, 0x4D, 0x18]) {
        "LZ4 frame"
    } else if starts(&[0x1F, 0x8B]) {
        "gzip"
    } else if head.len() >= 2 && head[0] == 0x78 && matches!(head[1], 0x01 | 0x9C | 0xDA) {
        "zlib (probable)"
    } else {
        "UNKNOWN"
    }
}

/// Shannon entropy in bits per byte.
pub fn entropy(data: &[u8]) -> f64 {
    if data.is_empty() {
        return 0.0;
    }
    let mut counts = [0usize; 256];
    data.iter().for_each(|b| counts[*b as usize] += 1);
    let n = data.len() as f64;
    counts.iter().filter(|c| **c > 0).map(|c| {
        let p = *c as f64 / n;
        -p * p.log2()
    }).sum()
}

pub fn run(args: &[String]) -> Result<(), String> {
    if args.is_empty() {
        return Err("usage: stardust magic <file>...".into());
    }
    for f in args {
        let data = std::fs::read(f).map_err(|e| format!("{f}: {e}"))?;
        let head: String = data.iter().take(32).map(|b| format!("{b:02X} ")).collect();
        println!(
            "{f}\n  size={} sha256={}\n  kind={}\n  first32={}\n  entropy={:.3} bits/byte",
            data.len(),
            crate::util::sha256_hex(&data),
            identify(&data),
            head.trim_end(),
            entropy(&data)
        );
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn identifies_known_and_unknown() {
        assert_eq!(identify(b"NUCC\0\0\0\x79"), "XFBIN (NUCC)");
        assert_eq!(identify(b"CRILAYLA\0\0"), "CRILAYLA compressed");
        assert_eq!(identify(&[0x78, 0x9C, 1]), "zlib (probable)");
        assert_eq!(identify(&[0x54, 0x09, 0x41, 0x02]), "UNKNOWN");
        assert!((entropy(&[0u8; 64]) - 0.0).abs() < 1e-9);
        assert!((entropy(&(0..=255u8).collect::<Vec<_>>()) - 8.0).abs() < 1e-9);
    }
}
