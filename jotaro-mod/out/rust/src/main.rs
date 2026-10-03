use std::env;
use std::ffi::OsString;
use std::fs::{self, File};
use std::io::{self, Read, Write};
use std::path::{Component, Path, PathBuf};
use std::process::{Command, ExitCode};

type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(err) => {
            eprintln!("error: {err}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<()> {
    let mut args: Vec<OsString> = env::args_os().skip(1).collect();
    if args.is_empty() || args[0] == "--help" || args[0] == "-h" || args[0] == "help" {
        print_help();
        return Ok(());
    }

    let tool = take_tool_arg(&mut args)?;
    let command = args[0].to_string_lossy().to_ascii_lowercase();
    match command.as_str() {
        "list" if args.len() == 2 => {
            let archive = PathBuf::from(&args[1]);
            require_cpk(&archive)?;
            run_tool(&tool, [OsString::from("-l"), archive.into_os_string()])
        }
        "extract" if args.len() == 3 => {
            let archive = PathBuf::from(&args[1]);
            require_cpk(&archive)?;
            validate_entry_paths(&tool, &archive)?;
            let output = prepare_output_dir(Path::new(&args[2]))?;
            run_tool(
                &tool,
                [
                    OsString::from("-e"),
                    archive.into_os_string(),
                    output.into_os_string(),
                ],
            )
        }
        "roundtrip" if args.len() == 3 => {
            let archive = PathBuf::from(&args[1]);
            require_cpk(&archive)?;
            let work = prepare_output_dir(Path::new(&args[2]))?;
            roundtrip(&tool, &archive, &work)
        }
        "catalog" if args.len() == 3 => {
            let root = PathBuf::from(&args[1]);
            if !root.is_dir() {
                return Err(format!("game root is not a directory: {}", root.display()).into());
            }
            let report = prepare_output_file(Path::new(&args[2]))?;
            catalog(&tool, &root, &report)
        }
        _ => {
            print_help();
            Err("invalid command or argument count".into())
        }
    }
}

fn print_help() {
    println!(
        "CC2 Asset CLI — safe CPK workflow for Storm 4 and ASBR\n\
         Usage:\n\
         \x20 cc2-asset-cli list <archive.cpk> [--tool <cpk-tool.exe>]\n\
         \x20 cc2-asset-cli extract <archive.cpk> <out-directory> [--tool <cpk-tool.exe>]\n\
         \x20 cc2-asset-cli roundtrip <archive.cpk> <out-work-directory> [--tool <cpk-tool.exe>]\n\
         \x20 cc2-asset-cli catalog <game-root> <out-report.txt> [--tool <cpk-tool.exe>]\n\n\
         All generated files must be under this project's out directory.\n\
         CPK list/extract/repack is delegated to the community cpk-tool utility.\n\
         Default tool path: out/tools/cpk-tool.exe"
    );
}

fn take_tool_arg(args: &mut Vec<OsString>) -> Result<PathBuf> {
    let mut selected = None;
    let mut index = 0;
    while index < args.len() {
        if args[index] == "--tool" {
            if selected.is_some() || index + 1 >= args.len() {
                return Err("--tool must occur once and include an executable path".into());
            }
            selected = Some(PathBuf::from(args.remove(index + 1)));
            args.remove(index);
        } else {
            index += 1;
        }
    }

    let path = selected.unwrap_or_else(|| project_out().join("tools/cpk-tool.exe"));
    if !path.is_file() {
        return Err(format!(
            "CPK helper not found at {}; download the documented cpk-tool release or pass --tool",
            path.display()
        )
        .into());
    }
    Ok(path)
}

fn project_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("manifest is expected at <project>/out/rust")
        .to_path_buf()
}

fn project_out() -> PathBuf {
    project_root().join("out")
}

fn normalized(path: &Path) -> Result<PathBuf> {
    let absolute = if path.is_absolute() {
        path.to_path_buf()
    } else {
        env::current_dir()?.join(path)
    };
    let mut result = PathBuf::new();
    for component in absolute.components() {
        match component {
            Component::CurDir => {}
            Component::ParentDir => {
                result.pop();
            }
            other => result.push(other.as_os_str()),
        }
    }
    Ok(result)
}

fn ensure_project_output(path: &Path) -> Result<PathBuf> {
    // Keep this comparison lexical: canonicalize() prefixes Windows paths with
    // `\\?\`, while the path supplied by the user may not have that prefix.
    let out = normalized(&project_out())?;
    let candidate = normalized(path)?;
    if !candidate.starts_with(&out) {
        return Err(format!(
            "output must be inside project out/: {}",
            candidate.display()
        )
        .into());
    }
    Ok(candidate)
}

fn prepare_output_dir(path: &Path) -> Result<PathBuf> {
    let candidate = ensure_project_output(path)?;
    fs::create_dir_all(&candidate)?;
    let canonical = fs::canonicalize(&candidate)?;
    let out = fs::canonicalize(project_out())?;
    if !canonical.starts_with(out) {
        return Err("output directory resolves outside project out/".into());
    }
    // Preserve the normal drive-letter path: the delegated CPK utility does
    // not accept the extended `\\?\` prefix returned by canonicalize().
    Ok(candidate)
}

fn prepare_output_file(path: &Path) -> Result<PathBuf> {
    let candidate = ensure_project_output(path)?;
    let parent = candidate
        .parent()
        .ok_or("report path has no parent directory")?;
    fs::create_dir_all(parent)?;
    let canonical_parent = fs::canonicalize(parent)?;
    let out = fs::canonicalize(project_out())?;
    if !canonical_parent.starts_with(out) {
        return Err("report path resolves outside project out/".into());
    }
    Ok(candidate)
}

fn require_cpk(path: &Path) -> Result<()> {
    if !path.is_file() {
        return Err(format!("archive not found: {}", path.display()).into());
    }
    let mut file = File::open(path)?;
    let mut magic = [0u8; 4];
    file.read_exact(&mut magic)?;
    if &magic != b"CPK " {
        return Err(format!("not a CRI CPK archive: {}", path.display()).into());
    }
    Ok(())
}

fn run_tool<I>(tool: &Path, args: I) -> Result<()>
where
    I: IntoIterator<Item = OsString>,
{
    let status = Command::new(tool).args(args).status()?;
    if !status.success() {
        return Err(format!("CPK helper returned {status}").into());
    }
    Ok(())
}

fn roundtrip(tool: &Path, archive: &Path, work: &Path) -> Result<()> {
    validate_entry_paths(tool, archive)?;
    let extracted = work.join("extracted");
    let rebuilt = work.join("rebuilt.cpk");
    if extracted.exists() || rebuilt.exists() {
        return Err(format!(
            "roundtrip outputs already exist under {}; choose a fresh directory",
            work.display()
        )
        .into());
    }
    fs::create_dir(&extracted)?;
    run_tool(
        tool,
        [
            OsString::from("-e"),
            archive.as_os_str().to_os_string(),
            extracted.as_os_str().to_os_string(),
        ],
    )?;
    run_tool(
        tool,
        [
            OsString::from("-p"),
            extracted.as_os_str().to_os_string(),
            rebuilt.as_os_str().to_os_string(),
        ],
    )?;
    compare_files(archive, &rebuilt)?;
    println!("Roundtrip is byte-identical: {}", archive.display());
    Ok(())
}

fn validate_entry_paths(tool: &Path, archive: &Path) -> Result<()> {
    let output = Command::new(tool).arg("-l").arg(archive).output()?;
    if !output.status.success() {
        return Err(format!(
            "could not list archive before extraction: {}",
            output.status
        )
        .into());
    }
    let listing = String::from_utf8_lossy(&output.stdout);
    let mut checked = 0usize;
    for line in listing.lines() {
        let mut columns = line.split_whitespace();
        let Some(id) = columns.next().and_then(|value| value.parse::<u64>().ok()) else {
            continue;
        };
        let Some(name) = columns.next() else {
            continue;
        };
        let entry = Path::new(name);
        if entry.is_absolute()
            || name.contains(':')
            || entry.components().any(|part| {
                matches!(part, Component::ParentDir | Component::Prefix(_))
            })
            || line.contains("../")
            || line.contains("..\\")
        {
            return Err(format!(
                "refusing to extract unsafe path from archive entry {id}: {name}"
            )
            .into());
        }
        checked += 1;
    }
    if checked == 0 && listing.contains("Files: ") && !listing.contains("Files: 0") {
        return Err("could not validate paths from the archive listing".into());
    }
    Ok(())
}

fn compare_files(left: &Path, right: &Path) -> Result<()> {
    let left_meta = fs::metadata(left)?;
    let right_meta = fs::metadata(right)?;
    if left_meta.len() != right_meta.len() {
        return Err(format!(
            "byte comparison failed: sizes differ ({} vs {})",
            left_meta.len(),
            right_meta.len()
        )
        .into());
    }
    let mut left_file = File::open(left)?;
    let mut right_file = File::open(right)?;
    let mut a = [0u8; 64 * 1024];
    let mut b = [0u8; 64 * 1024];
    loop {
        let read_a = left_file.read(&mut a)?;
        let read_b = right_file.read(&mut b)?;
        if read_a != read_b || a[..read_a] != b[..read_b] {
            return Err("byte comparison failed: archive contents differ".into());
        }
        if read_a == 0 {
            break;
        }
    }
    Ok(())
}

fn catalog(tool: &Path, root: &Path, report_path: &Path) -> Result<()> {
    let root = normalized(root)?;
    let mut files = Vec::new();
    collect_files(&root, &root, &mut files)?;
    files.sort();

    let mut report = File::create(report_path)?;
    writeln!(report, "CC2 game tree catalog")?;
    writeln!(report, "Root: {}", root.display())?;
    writeln!(report, "Generated by cc2-asset-cli; archive entries delegated to cpk-tool")?;
    let mut archive_count = 0usize;
    let mut loose_xfbin_count = 0usize;
    let mut errors = Vec::new();

    writeln!(report, "\n## Loose XFBIN files\n")?;
    for (path, relative) in files.iter().filter(|(path, _)| extension_is(path, "xfbin")) {
        let length = fs::metadata(path)?.len();
        let mut file = File::open(path)?;
        let mut magic = [0u8; 4];
        let read = file.read(&mut magic)?;
        let signature = String::from_utf8_lossy(&magic[..read]);
        writeln!(report, "{relative}\t{length}\t{signature}")?;
        loose_xfbin_count += 1;
    }

    for (archive, relative) in files.iter().filter(|(path, _)| extension_is(path, "cpk")) {
        archive_count += 1;
        writeln!(report, "\n## CPK: {relative}\n")?;
        let result = Command::new(tool).arg("-l").arg(archive).output()?;
        report.write_all(&result.stdout)?;
        if !result.status.success() {
            errors.push(format!("{relative}: {}", result.status));
            writeln!(report, "\n[listing failed: {}]", result.status)?;
            report.write_all(&result.stderr)?;
        }
    }
    report.flush()?;
    println!(
        "Cataloged {archive_count} CPK archives and {loose_xfbin_count} loose XFBINs to {}",
        report_path.display()
    );
    if errors.is_empty() {
        Ok(())
    } else {
        Err(format!(
            "{} archive listing(s) failed; see the catalog report",
            errors.len()
        )
        .into())
    }
}

fn collect_files(root: &Path, directory: &Path, files: &mut Vec<(PathBuf, String)>) -> Result<()> {
    for entry in fs::read_dir(directory)? {
        let entry = entry?;
        let kind = entry.file_type()?;
        if kind.is_symlink() {
            continue;
        }
        let path = entry.path();
        if kind.is_dir() {
            collect_files(root, &path, files)?;
        } else if kind.is_file()
            && (extension_is(&path, "cpk") || extension_is(&path, "xfbin"))
        {
            let relative = path
                .strip_prefix(root)?
                .to_string_lossy()
                .replace('\\', "/");
            files.push((path, relative));
        }
    }
    Ok(())
}

fn extension_is(path: &Path, expected: &str) -> bool {
    path.extension()
        .and_then(|ext| ext.to_str())
        .is_some_and(|ext| ext.eq_ignore_ascii_case(expected))
}

#[allow(dead_code)]
fn _ensure_output_is_writable(path: &Path) -> io::Result<()> {
    let mut file = File::open(path)?;
    let mut byte = [0u8; 1];
    let _ = file.read(&mut byte)?;
    Ok(())
}

