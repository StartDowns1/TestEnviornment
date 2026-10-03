param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('launch', 'install', 'uninstall')]
    [string] $Action
)

$ErrorActionPreference = 'Stop'
$statePath = Join-Path $PSScriptRoot 'install-state.json'
$defaultGameRoot = ''
$defaultPayloadRoot = Join-Path $PSScriptRoot 'payload'
$gameModId = 'Jotaro body-only slot replacement'

function Get-CanonicalPath([string] $Path) {
    $full = [System.IO.Path]::GetFullPath($Path.Trim().Trim('"'))
    $root = [System.IO.Path]::GetPathRoot($full)
    if ([string]::Equals($full, $root, [System.StringComparison]::OrdinalIgnoreCase)) { return $full }
    return $full.TrimEnd('\')
}

function Read-Path([string] $Prompt, [string] $Default, [switch] $MustExist) {
    while ($true) {
        $answer = Read-Host "$Prompt (Enter keeps: $Default)"
        if ([string]::IsNullOrWhiteSpace($answer)) {
            if ([string]::IsNullOrWhiteSpace($Default)) {
                Write-Host 'A path is required.' -ForegroundColor Yellow
                continue
            }
            $answer = $Default
        }
        try { $candidate = Get-CanonicalPath $answer } catch {
            Write-Host 'That path is not valid. Try again.' -ForegroundColor Yellow
            continue
        }
        if (-not $MustExist -or (Test-Path -LiteralPath $candidate)) { return $candidate }
        Write-Host "Path does not exist: $candidate" -ForegroundColor Yellow
    }
}

function Get-FileSha256([string] $Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Read-State {
    if (-not (Test-Path -LiteralPath $statePath)) { return $null }
    return Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
}

function Write-State($State) {
    $json = ConvertTo-Json -InputObject $State -Depth 12
    [System.IO.File]::WriteAllText($statePath, $json + "`r`n", [System.Text.UTF8Encoding]::new($false))
}

function Mark-Restored($Entry) {
    if ($Entry.PSObject.Properties['restored']) {
        $Entry.restored = $true
    } else {
        $Entry | Add-Member -NotePropertyName 'restored' -NotePropertyValue $true
    }
}

function Confirm-Offline {
    Write-Host 'This launcher only supports an offline test.' -ForegroundColor Cyan
    $answer = Read-Host 'Type OFFLINE to confirm you will use the game offline'
    if ($answer -cne 'OFFLINE') {
        Write-Host 'Cancelled. No files were installed and the game was not started.' -ForegroundColor Yellow
        return $false
    }
    return $true
}

function Install-Payload([string] $GameRoot, [string] $PayloadRoot) {
    $modRoot = Join-Path $PayloadRoot 'data_win32'
    if (-not (Test-Path -LiteralPath $modRoot -PathType Container)) {
        throw "Payload folder must contain data_win32: $PayloadRoot"
    }
    $files = @(Get-ChildItem -LiteralPath $modRoot -File -Recurse | Sort-Object FullName)
    if ($files.Count -eq 0) { throw "No payload files were found under $PayloadRoot" }

    $state = Read-State
    if ($state -and -not [string]::Equals((Get-CanonicalPath $state.gameRoot), $GameRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "A different game folder is managed in $statePath. Uninstall that copy before switching folders."
    }
    if (-not $state) {
        $state = [pscustomobject]@{
            schemaVersion = 1
            mod = $gameModId
            gameRoot = $GameRoot
            payloadRoot = $PayloadRoot
            installedAt = (Get-Date).ToUniversalTime().ToString('o')
            createdDirectories = @()
            files = @()
        }
    }

    foreach ($source in $files) {
        $relative = $source.FullName.Substring($PayloadRoot.TrimEnd('\').Length).TrimStart('\')
        if ([string]::IsNullOrWhiteSpace($relative) -or $relative.Split('\') -contains '..') {
            throw "Unsafe payload-relative path: $relative"
        }
        $destination = [System.IO.Path]::GetFullPath((Join-Path $GameRoot $relative))
        if (-not $destination.StartsWith($GameRoot.TrimEnd('\') + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Payload path escapes the game folder: $relative"
        }

        $newHash = Get-FileSha256 $source.FullName
        $managed = @($state.files | Where-Object { [string]::Equals($_.relativePath, $relative, [System.StringComparison]::OrdinalIgnoreCase) }) | Select-Object -First 1
        $destinationExists = Test-Path -LiteralPath $destination
        $currentHash = if ($destinationExists) { Get-FileSha256 $destination } else { $null }
        if ($destinationExists -and ($currentHash -eq $newHash)) {
            if (-not $managed) {
                throw "The target already matches the payload but has no restore record: $destination. Refusing to claim or overwrite it."
            }
            $managed.installedSha256 = $newHash
            continue
        }
        if ($managed -and $destinationExists -and ($currentHash -ne $managed.installedSha256)) {
            throw "The managed target changed since install; refusing to overwrite it: $destination"
        }

        $dir = Split-Path -Parent $destination
        $missingDirs = @()
        $cursor = $dir
        while ($cursor.StartsWith($GameRoot, [System.StringComparison]::OrdinalIgnoreCase) -and -not (Test-Path -LiteralPath $cursor)) {
            $missingDirs += $cursor
            $parent = Split-Path -Parent $cursor
            if ($parent -eq $cursor) { break }
            $cursor = $parent
        }
        [array]::Reverse($missingDirs)
        foreach ($missingDir in $missingDirs) {
            New-Item -ItemType Directory -Path $missingDir | Out-Null
            $relativeDir = $missingDir.Substring($GameRoot.TrimEnd('\').Length).TrimStart('\')
            if ($relativeDir -and $state.createdDirectories -notcontains $relativeDir) {
                $state.createdDirectories += $relativeDir
            }
        }

        if ($managed) {
            if ($managed.originalExisted -and $managed.backupPath -and -not (Test-Path -LiteralPath $managed.backupPath)) {
                throw "Saved original override is missing: $($managed.backupPath)"
            }
        } else {
            $originalExisted = $destinationExists
            $backupPath = $null
            $originalHash = $null
            if ($originalExisted) {
                $originalHash = Get-FileSha256 $destination
                $backupDir = Join-Path $PSScriptRoot (Join-Path 'backups' (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
                $backupPath = Join-Path $backupDir $relative
                New-Item -ItemType Directory -Force -Path (Split-Path -Parent $backupPath) | Out-Null
                Copy-Item -LiteralPath $destination -Destination $backupPath
                if ((Get-FileSha256 $backupPath) -ne $originalHash) { throw "Backup verification failed for $destination" }
            }
            $managed = [pscustomobject]@{
                relativePath = $relative
                originalExisted = $originalExisted
                originalSha256 = $originalHash
                backupPath = $backupPath
                installedSha256 = $newHash
            }
            $state.files += $managed
        }

        Write-State $state
        Copy-Item -LiteralPath $source.FullName -Destination $destination -Force
        if ((Get-FileSha256 $destination) -ne $newHash) { throw "Installed-file verification failed: $destination" }
        $managed.installedSha256 = $newHash
        Write-State $state
        Write-Host "Installed $relative"
    }

    $state.payloadRoot = $PayloadRoot
    Write-State $state
}

function Uninstall-Payload([string] $GameRoot) {
    $state = Read-State
    if (-not $state) { throw "No install record exists at $statePath. Nothing was changed." }
    if (-not [string]::Equals((Get-CanonicalPath $state.gameRoot), $GameRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "The requested game folder does not match the recorded install: $($state.gameRoot)"
    }

    $conflicts = 0
    foreach ($entry in @($state.files)) {
        $target = [System.IO.Path]::GetFullPath((Join-Path $GameRoot $entry.relativePath))
        if (-not $target.StartsWith($GameRoot.TrimEnd('\') + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
            $conflicts++
            Write-Host "Unsafe restore path in install record: $($entry.relativePath)" -ForegroundColor Red
            continue
        }
        if ($entry.restored) {
            if ($entry.originalExisted -and (Test-Path -LiteralPath $target) -and (Get-FileSha256 $target) -eq $entry.originalSha256) {
                Write-Host "Original already restored: $($entry.relativePath)"
                continue
            }
            if (-not $entry.originalExisted -and -not (Test-Path -LiteralPath $target)) {
                Write-Host "Added override already removed: $($entry.relativePath)"
                continue
            }
            $conflicts++
            Write-Host "Previously restored target changed again; left untouched: $($entry.relativePath)" -ForegroundColor Yellow
            continue
        }
        if (-not (Test-Path -LiteralPath $target)) {
            if ($entry.originalExisted) {
                if (-not (Test-Path -LiteralPath $entry.backupPath)) { $conflicts++; Write-Host "Missing target and backup: $($entry.relativePath)" -ForegroundColor Red; continue }
                if ((Get-FileSha256 $entry.backupPath) -ne $entry.originalSha256) { $conflicts++; Write-Host "Backup hash mismatch: $($entry.relativePath)" -ForegroundColor Red; continue }
                New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
                Copy-Item -LiteralPath $entry.backupPath -Destination $target
                Mark-Restored $entry
                Write-State $state
                Write-Host "Restored original override: $($entry.relativePath)"
            } else {
                Write-Host "Already removed: $($entry.relativePath)"
                Mark-Restored $entry
                Write-State $state
            }
            continue
        }

        if ((Get-FileSha256 $target) -ne $entry.installedSha256) {
            $conflicts++
            Write-Host "Left changed file untouched: $($entry.relativePath)" -ForegroundColor Yellow
            continue
        }
        if ($entry.originalExisted) {
            if (-not (Test-Path -LiteralPath $entry.backupPath)) { $conflicts++; Write-Host "Backup is missing: $($entry.relativePath)" -ForegroundColor Red; continue }
            if ((Get-FileSha256 $entry.backupPath) -ne $entry.originalSha256) { $conflicts++; Write-Host "Backup hash mismatch: $($entry.relativePath)" -ForegroundColor Red; continue }
            Copy-Item -LiteralPath $entry.backupPath -Destination $target -Force
            Mark-Restored $entry
            Write-State $state
            Write-Host "Restored original override: $($entry.relativePath)"
        } else {
            Remove-Item -LiteralPath $target
            Mark-Restored $entry
            Write-State $state
            Write-Host "Removed added override: $($entry.relativePath)"
        }
    }

    foreach ($relativeDir in @($state.createdDirectories | Sort-Object Length -Descending)) {
        $directory = Join-Path $GameRoot $relativeDir
        if ((Test-Path -LiteralPath $directory) -and -not (Get-ChildItem -LiteralPath $directory -Force | Select-Object -First 1)) {
            Remove-Item -LiteralPath $directory
        }
    }
    if ($conflicts -eq 0) {
        Remove-Item -LiteralPath $statePath
        Write-Host 'Mod override(s) restored. Backup copies remain under out\phase5\backups.' -ForegroundColor Green
    } else {
        Write-Host "$conflicts item(s) need attention; the install record was kept." -ForegroundColor Yellow
        exit 2
    }
}

try {
    $existingState = Read-State
    if ($Action -eq 'uninstall') {
        if (Get-Process -Name 'NSUNS4' -ErrorAction SilentlyContinue) {
            throw 'Storm 4 is running. Close it before uninstalling the mod.'
        }
        $gameDefault = if ($existingState) { $existingState.gameRoot } else { $defaultGameRoot }
        $gameRoot = Read-Path 'Storm 4 folder' $gameDefault -MustExist
        Uninstall-Payload $gameRoot
        exit 0
    }

    if (-not (Confirm-Offline)) { exit 1 }
    if (Get-Process -Name 'NSUNS4' -ErrorAction SilentlyContinue) {
        throw 'Storm 4 is already running. Close it, then start this launcher again.'
    }
    $gameDefault = if ($existingState) { $existingState.gameRoot } else { $defaultGameRoot }
    $gameRoot = Read-Path 'Storm 4 folder containing NSUNS4.exe' $gameDefault -MustExist
    $exe = Join-Path $gameRoot 'NSUNS4.exe'
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
        $exe = Read-Path 'Full path to NSUNS4.exe' (Join-Path $gameRoot 'NSUNS4.exe') -MustExist
        if ((Split-Path -Leaf $exe) -ine 'NSUNS4.exe') { throw 'Selected file is not NSUNS4.exe' }
        $gameRoot = Split-Path -Parent $exe
    }
    $payloadRoot = $defaultPayloadRoot
    if (-not (Test-Path -LiteralPath $payloadRoot -PathType Container) -or -not (Get-ChildItem -LiteralPath $payloadRoot -File -Recurse | Select-Object -First 1)) {
        $payloadRoot = Read-Path 'Folder containing the mod payload (must contain data_win32)' $defaultPayloadRoot -MustExist
    }
    if (-not (Test-Path -LiteralPath (Join-Path $payloadRoot 'data_win32') -PathType Container)) {
        throw "Payload folder must contain a data_win32 subfolder: $payloadRoot"
    }

    Install-Payload $gameRoot $payloadRoot
    if ($Action -eq 'install') {
        Write-Host 'Mod files installed. Close this window, then use Launch_Jotaro_Mod.bat for an offline launch.' -ForegroundColor Green
        exit 0
    }
    Write-Host 'Starting Storm 4. Do not select online modes.' -ForegroundColor Cyan
    $process = Start-Process -FilePath $exe -WorkingDirectory $gameRoot -PassThru
    Write-Host "Started NSUNS4.exe (PID $($process.Id))." -ForegroundColor Green
    exit 0
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

