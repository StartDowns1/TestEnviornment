<#
.SYNOPSIS
  Stardust Storm installer / uninstaller (offline, personal use).

.DESCRIPTION
  Installs a payload built by `stardust build` (a folder with manifest.json) into a Storm 4
  folder and restores it exactly. Guarantees kept from out/phase5/modctl.ps1:
    - every installed file is hash-tracked; uninstall only removes/restores files whose hash
      still matches what we installed; changed files are left alone and reported
    - originals are backed up and the backup hash is verified before overwriting
    - directories we create are recorded and removed only when empty
    - refuses to run while NSUNS4 is running; requires typed OFFLINE confirmation
  Added: -DryRun, several named payload sets in one state file, manifest verification,
  and an -AllowModifyOriginals gate (plus typed confirmation) for replacing files that
  already exist in the game folder (Variant C: loose .gfx).

.EXAMPLE
  pwsh installer/stardust.ps1 -Action install -Payload out/payload/ladder/L0 -Set L0 -DryRun
#>
param(
    [Parameter(Mandatory = $true)][ValidateSet('install', 'uninstall', 'status', 'launch')][string] $Action,
    [string] $GameRoot,
    [string] $Payload,
    [string] $Set,
    [switch] $DryRun,
    [switch] $AllowModifyOriginals,
    [string] $Confirmation,          # pass OFFLINE to skip the prompt (tests); otherwise prompted
    [string] $OriginalsConfirmation, # pass "MODIFY ORIGINALS" to skip that prompt (tests)
    [string] $StatePath,
    [string] $ProcessName = 'NSUNS4'
)

$ErrorActionPreference = 'Stop'
$sep = [System.IO.Path]::DirectorySeparatorChar
$cmp = [System.StringComparison]::OrdinalIgnoreCase
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $StatePath) { $StatePath = Join-Path $PSScriptRoot (Join-Path 'state' 'stardust-state.json') }
$backupRoot = Join-Path (Split-Path -Parent $StatePath) 'backups'

function Get-Canonical([string] $Path) {
    $full = [System.IO.Path]::GetFullPath($Path.Trim().Trim('"'))
    if ($full.Length -gt 1) { $full = $full.TrimEnd('\', '/') }
    return $full
}
function Get-Sha([string] $Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function Join-Rel([string] $Root, [string] $Rel) { Join-Path $Root ($Rel -replace '[\\/]', $sep) }
function Test-Inside([string] $Root, [string] $Path) { $Path.StartsWith($Root + $sep, $cmp) }

function Read-State {
    if (Test-Path -LiteralPath $StatePath) { return Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json }
    return $null
}
function Write-State($State) {
    if ($DryRun) { return }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $StatePath) | Out-Null
    $json = ConvertTo-Json -InputObject $State -Depth 12
    [System.IO.File]::WriteAllText($StatePath, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
}
function Get-SetRecord($State, [string] $Name) { @($State.sets | Where-Object { $_.name -eq $Name }) | Select-Object -First 1 }

function Resolve-GameRoot($State) {
    if ($GameRoot) { return Get-Canonical $GameRoot }
    if ($State) { return $State.gameRoot }
    # Reuse the folder the legacy Phase 5 launcher remembered, if any.
    $legacy = Join-Path $projectRoot (Join-Path 'out' (Join-Path 'phase5' 'install-state.json'))
    if (Test-Path -LiteralPath $legacy) { return (Get-Content -LiteralPath $legacy -Raw | ConvertFrom-Json).gameRoot }
    throw 'No -GameRoot given and none remembered. Pass -GameRoot <Storm 4 folder>.'
}

function Assert-Offline {
    $answer = if ($Confirmation) { $Confirmation } else { Read-Host 'Offline, single-player use only. Type OFFLINE to continue' }
    if ($answer -cne 'OFFLINE') { throw 'Not confirmed. Nothing was changed.' }
}
function Assert-NotRunning {
    if (Get-Process -Name $ProcessName -ErrorAction SilentlyContinue) { throw "$ProcessName is running. Close it first. Nothing was changed." }
}
function Say([string] $Text, [string] $Color = 'Gray') {
    $prefix = if ($DryRun) { '[dry-run] ' } else { '' }
    Write-Host ($prefix + $Text) -ForegroundColor $Color
}

function Install-Set {
    if (-not $Payload -or -not $Set) { throw 'install needs -Payload <dir with manifest.json> and -Set <name>' }
    $payloadRoot = Get-Canonical $Payload
    $manifestPath = Join-Path $payloadRoot 'manifest.json'
    if (-not (Test-Path -LiteralPath $manifestPath)) { throw "No manifest.json in $payloadRoot (build it with: stardust build)" }
    # -InputObject (not a pipeline) so Windows PowerShell 5.1 yields one item per array element.
    $manifest = @(ConvertFrom-Json -InputObject (Get-Content -LiteralPath $manifestPath -Raw))
    $entries = @($manifest | Where-Object { $_.path -like 'data_win32/*' })
    if ($entries.Count -eq 0) { throw "Manifest lists no data_win32/ files: $manifestPath" }

    $state = Read-State
    $game = Resolve-GameRoot $state
    if (-not (Test-Path -LiteralPath $game -PathType Container)) { throw "Game folder not found: $game" }
    if ($state -and -not [string]::Equals($state.gameRoot, $game, $cmp)) { throw "State file manages a different game folder ($($state.gameRoot)). Uninstall it first." }
    if (-not $state) { $state = [pscustomobject]@{ schemaVersion = 2; gameRoot = $game; sets = @() } }
    if (Get-SetRecord $state $Set) { throw "Set '$Set' is already installed. Uninstall it first." }

    # Pass 1: plan and validate everything before touching anything.
    $plan = @()
    foreach ($e in $entries) {
        $rel = $e.path -replace '\\', '/'
        if ($rel.Split('/') -contains '..') { throw "Unsafe path in manifest: $rel" }
        $src = Join-Rel $payloadRoot $rel
        if (-not (Test-Path -LiteralPath $src -PathType Leaf)) { throw "Manifest file missing from payload: $rel" }
        $hash = Get-Sha $src
        if ($hash -ne $e.sha256.ToUpperInvariant()) { throw "Payload file does not match manifest hash: $rel" }
        $dst = [System.IO.Path]::GetFullPath((Join-Rel $game $rel))
        if (-not (Test-Inside $game $dst)) { throw "Path escapes the game folder: $rel" }
        foreach ($other in @($state.sets)) {
            if (@($other.files | Where-Object { [string]::Equals($_.relativePath, $rel, $cmp) }).Count) { throw "$rel is already managed by set '$($other.name)'" }
        }
        $exists = Test-Path -LiteralPath $dst
        $plan += [pscustomobject]@{ rel = $rel; src = $src; dst = $dst; hash = $hash; exists = $exists }
    }
    $originals = @($plan | Where-Object { $_.exists })
    foreach ($p in $plan) { Say ("{0} {1}" -f ($(if ($p.exists) { 'REPLACE (backup first)' } else { 'ADD    ' })), $p.rel) }
    if ($originals.Count -gt 0) {
        if (-not $AllowModifyOriginals) {
            throw "$($originals.Count) file(s) already exist in the game folder. Replacing originals needs -AllowModifyOriginals. Nothing was changed."
        }
        if (-not $DryRun) {
            $ok = if ($OriginalsConfirmation) { $OriginalsConfirmation } else { Read-Host 'This modifies ORIGINAL game files (backed up first). Type MODIFY ORIGINALS' }
            if ($ok -cne 'MODIFY ORIGINALS') { throw 'Not confirmed. Nothing was changed.' }
        }
    }
    if ($DryRun) { Say "$($plan.Count) file(s) would be installed as set '$Set'; $($originals.Count) original(s) would be backed up." 'Cyan'; return }

    $record = [pscustomobject]@{ name = $Set; payload = $payloadRoot; installedAt = (Get-Date).ToUniversalTime().ToString('o'); createdDirectories = @(); files = @() }
    $state.sets = @($state.sets) + $record
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
    foreach ($p in $plan) {
        $missing = @()
        $cursor = Split-Path -Parent $p.dst
        while ((Test-Inside $game $cursor) -and -not (Test-Path -LiteralPath $cursor)) { $missing += $cursor; $cursor = Split-Path -Parent $cursor }
        [array]::Reverse($missing)
        foreach ($d in $missing) {
            New-Item -ItemType Directory -Path $d | Out-Null
            $record.createdDirectories = @($record.createdDirectories) + $d.Substring($game.Length + 1)
        }
        $f = [pscustomobject]@{ relativePath = $p.rel; originalExisted = $p.exists; originalSha256 = $null; backupPath = $null; installedSha256 = $p.hash; restored = $false }
        if ($p.exists) {
            $f.originalSha256 = Get-Sha $p.dst
            $f.backupPath = Join-Rel (Join-Path $backupRoot (Join-Path $Set $stamp)) $p.rel
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $f.backupPath) | Out-Null
            Copy-Item -LiteralPath $p.dst -Destination $f.backupPath
            if ((Get-Sha $f.backupPath) -ne $f.originalSha256) { throw "Backup verification failed: $($p.rel)" }
        }
        $record.files = @($record.files) + $f
        Write-State $state   # record before copying so an interrupted run is still restorable
        Copy-Item -LiteralPath $p.src -Destination $p.dst -Force
        if ((Get-Sha $p.dst) -ne $p.hash) { throw "Installed-file verification failed: $($p.rel)" }
        Say "Installed $($p.rel)" 'Green'
    }
    Write-State $state
    Say "Set '$Set' installed: $($plan.Count) file(s). State: $StatePath" 'Green'
}

function Uninstall-Set {
    $state = Read-State
    if (-not $state) { throw "No install state at $StatePath. Nothing to do." }
    $game = $state.gameRoot
    $targets = if ($Set) { @(Get-SetRecord $state $Set) } else { @($state.sets) }
    if ($Set -and -not $targets[0]) { throw "Set '$Set' is not installed." }
    $conflicts = 0
    foreach ($rec in $targets) {
        foreach ($f in @($rec.files)) {
            if ($f.restored) { continue }
            $dst = [System.IO.Path]::GetFullPath((Join-Rel $game $f.relativePath))
            if (-not (Test-Inside $game $dst)) { $conflicts++; Say "Unsafe path in state: $($f.relativePath)" 'Red'; continue }
            $present = Test-Path -LiteralPath $dst
            if ($present -and (Get-Sha $dst) -ne $f.installedSha256) {
                if ($f.originalExisted -and (Get-Sha $dst) -eq $f.originalSha256) { Say "Already original: $($f.relativePath)"; $f.restored = $true; Write-State $state; continue }
                $conflicts++; Say "Changed since install; left untouched: $($f.relativePath)" 'Yellow'; continue
            }
            if ($f.originalExisted) {
                if (-not (Test-Path -LiteralPath $f.backupPath) -or (Get-Sha $f.backupPath) -ne $f.originalSha256) { $conflicts++; Say "Backup missing or corrupt: $($f.relativePath)" 'Red'; continue }
                Say "Restore original $($f.relativePath)"
                if (-not $DryRun) { Copy-Item -LiteralPath $f.backupPath -Destination $dst -Force }
            } elseif ($present) {
                Say "Remove $($f.relativePath)"
                if (-not $DryRun) { Remove-Item -LiteralPath $dst }
            }
            if (-not $DryRun) { $f.restored = $true; Write-State $state }
        }
        foreach ($d in @($rec.createdDirectories | Sort-Object Length -Descending)) {
            $dir = Join-Rel $game $d
            if ((Test-Path -LiteralPath $dir) -and -not (Get-ChildItem -LiteralPath $dir -Force | Select-Object -First 1)) {
                Say "Remove empty directory $d"
                if (-not $DryRun) { Remove-Item -LiteralPath $dir }
            }
        }
        if (-not $DryRun -and -not @($rec.files | Where-Object { -not $_.restored }).Count) {
            $state.sets = @($state.sets | Where-Object { $_.name -ne $rec.name })
            Write-State $state
            Say "Set '$($rec.name)' removed." 'Green'
        }
    }
    if (-not $DryRun -and @($state.sets).Count -eq 0) { Remove-Item -LiteralPath $StatePath; Say 'All sets removed; state file deleted. Backups are kept.' 'Green' }
    if ($conflicts) { Say "$conflicts item(s) need attention; their records were kept." 'Yellow'; exit 2 }
}

try {
    switch ($Action) {
        'status' {
            $s = Read-State
            if (-not $s) { Write-Host 'Nothing installed.'; exit 0 }
            Write-Host "Game: $($s.gameRoot)"
            foreach ($r in @($s.sets)) { Write-Host (" set {0}: {1} file(s), installed {2}" -f $r.name, @($r.files).Count, $r.installedAt) }
            exit 0
        }
        'install' { Assert-NotRunning; if (-not $DryRun) { Assert-Offline }; Install-Set; exit 0 }
        'uninstall' { Assert-NotRunning; Uninstall-Set; exit 0 }
        'launch' {
            # Install -Payload as -Set (unless that set is already installed), then start the game offline.
            Assert-NotRunning; Assert-Offline
            $s = Read-State
            $exeCheck = Join-Path (Resolve-GameRoot $s) 'NSUNS4.exe'
            if (-not (Test-Path -LiteralPath $exeCheck -PathType Leaf)) { throw "NSUNS4.exe not found at $exeCheck. Nothing was changed." }
            if ($Payload -and $Set -and -not ($s -and (Get-SetRecord $s $Set))) { Install-Set }
            $s = Read-State
            if (-not $s -or -not @($s.sets).Count) { throw 'No mod set is installed. Pass -Payload and -Set.' }
            $game = Resolve-GameRoot $s
            $exe = Join-Path $game 'NSUNS4.exe'
            if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw "NSUNS4.exe not found in $game" }
            Write-Host ("Active sets: " + (@($s.sets).name -join ', ')) -ForegroundColor Cyan
            if ($DryRun) { Say "Would start $exe"; exit 0 }
            Write-Host 'Starting Storm 4. Do not select online modes.' -ForegroundColor Cyan
            $p = Start-Process -FilePath $exe -WorkingDirectory $game -PassThru
            Write-Host "Started NSUNS4.exe (PID $($p.Id))." -ForegroundColor Green
            exit 0
        }
    }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
