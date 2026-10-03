# Mock-folder tests for installer/stardust.ps1. Never touches a real game folder:
# everything lives under out/mock-installer-test/ and is deleted at the start.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$work = Join-Path $root (Join-Path 'out' 'mock-installer-test')
if (Test-Path $work) { Remove-Item -Recurse -Force $work }
$game = Join-Path $work 'game'; $state = Join-Path $work (Join-Path 'state' 's.json')
$inst = Join-Path $PSScriptRoot 'stardust.ps1'
$script:fail = 0
function Check([bool] $ok, [string] $what) { if ($ok) { Write-Host "PASS $what" } else { Write-Host "FAIL $what" -ForegroundColor Red; $script:fail++ } }
function Sha($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
function Payload([string] $name, [hashtable] $files) {
    $dir = Join-Path $work $name; $m = @()
    foreach ($k in $files.Keys) {
        $p = Join-Path $dir $k; New-Item -ItemType Directory -Force (Split-Path -Parent $p) | Out-Null
        [IO.File]::WriteAllText($p, $files[$k]); $m += [pscustomobject]@{ path = $k; size = (Get-Item $p).Length; sha256 = Sha $p }
    }
    ConvertTo-Json -InputObject @($m) | Set-Content (Join-Path $dir 'manifest.json'); return $dir
}
function Run([string[]] $a) { & pwsh -NoProfile -File $inst @a -GameRoot $game -StatePath $state -Confirmation OFFLINE *> $null; return $LASTEXITCODE }

New-Item -ItemType Directory -Force (Join-Path $game 'data_win32/ui') | Out-Null
[IO.File]::WriteAllText((Join-Path $game 'data_win32/ui/title.gfx'), 'ORIGINAL-TITLE')
$origHash = Sha (Join-Path $game 'data_win32/ui/title.gfx')
$pA = Payload 'payA' @{ 'data_win32/spc/1nrtbod1.xfbin' = 'JOTARO'; 'data_win32/spcload/x.xfbin' = 'LOAD' }
$pC = Payload 'payC' @{ 'data_win32/ui/title.gfx' = 'STARDUST-TITLE' }
$pBad = Payload 'payBad' @{ 'data_win32/spc/z.xfbin' = 'Z' }; [IO.File]::WriteAllText((Join-Path $pBad 'data_win32/spc/z.xfbin'), 'TAMPERED')

Check ((Run @('-Action','install','-Payload',$pA,'-Set','A','-DryRun')) -eq 0 -and -not (Test-Path (Join-Path $game 'data_win32/spc')) -and -not (Test-Path $state)) 'dry-run changes nothing'
Check ($(& pwsh -NoProfile -File $inst -Action install -Payload $pA -Set A -GameRoot $game -StatePath $state -Confirmation nope *> $null; $LASTEXITCODE) -eq 1 -and -not (Test-Path $state)) 'missing OFFLINE refuses'
Check ((Run @('-Action','install','-Payload',$pBad,'-Set','Bad')) -eq 1 -and -not (Test-Path (Join-Path $game 'data_win32/spc'))) 'tampered payload refused before any write'
Check ((Run @('-Action','install','-Payload',$pA,'-Set','A')) -eq 0 -and (Get-Content (Join-Path $game 'data_win32/spc/1nrtbod1.xfbin')) -eq 'JOTARO') 'install set A'
Check ((Run @('-Action','install','-Payload',$pA,'-Set','A2')) -eq 1) 'same file in a second set refused'
Check ((Run @('-Action','install','-Payload',$pC,'-Set','C')) -eq 1 -and (Sha (Join-Path $game 'data_win32/ui/title.gfx')) -eq $origHash) 'original replacement refused without -AllowModifyOriginals'
Check ((Run @('-Action','install','-Payload',$pC,'-Set','C','-AllowModifyOriginals','-OriginalsConfirmation','no')) -eq 1 -and (Sha (Join-Path $game 'data_win32/ui/title.gfx')) -eq $origHash) 'originals gate needs typed confirmation'
Check ((Run @('-Action','install','-Payload',$pC,'-Set','C','-AllowModifyOriginals','-OriginalsConfirmation','MODIFY ORIGINALS')) -eq 0 -and (Get-Content (Join-Path $game 'data_win32/ui/title.gfx')) -eq 'STARDUST-TITLE') 'Variant C install with backup'
[IO.File]::WriteAllText((Join-Path $game 'data_win32/spcload/x.xfbin'), 'USER-EDIT')
Check ((Run @('-Action','uninstall','-Set','A')) -eq 2 -and (Get-Content (Join-Path $game 'data_win32/spcload/x.xfbin')) -eq 'USER-EDIT' -and -not (Test-Path (Join-Path $game 'data_win32/spc/1nrtbod1.xfbin'))) 'changed file left untouched, others removed, exit 2'
[IO.File]::WriteAllText((Join-Path $game 'data_win32/spcload/x.xfbin'), 'LOAD')
Check ((Run @('-Action','uninstall','-Set','A')) -eq 0 -and -not (Test-Path (Join-Path $game 'data_win32/spcload')) -and -not (Test-Path (Join-Path $game 'data_win32/spc'))) 'retry after conflict succeeds; created dirs removed'
Check ((Run @('-Action','uninstall','-DryRun')) -eq 0 -and (Get-Content (Join-Path $game 'data_win32/ui/title.gfx')) -eq 'STARDUST-TITLE') 'uninstall dry-run changes nothing'
Check ((Run @('-Action','uninstall')) -eq 0 -and (Sha (Join-Path $game 'data_win32/ui/title.gfx')) -eq $origHash -and -not (Test-Path $state)) 'original restored byte-exact; state removed'
Check ((Test-Path (Join-Path $game 'data_win32/ui')) -and @(Get-ChildItem -Recurse -File $game).Count -eq 1) 'pre-existing directories kept; game tree back to original'
$fake = Start-Process -FilePath (Get-Command sleep).Source -ArgumentList 30 -PassThru
Check ($(& pwsh -NoProfile -File $inst -Action install -Payload $pA -Set A -GameRoot $game -StatePath $state -Confirmation OFFLINE -ProcessName $fake.ProcessName *> $null; $LASTEXITCODE) -eq 1 -and -not (Test-Path $state)) 'refuses while game process runs'
Stop-Process -Id $fake.Id
if ($script:fail) { Write-Host "$script:fail test(s) FAILED" -ForegroundColor Red; exit 1 } else { Write-Host 'ALL INSTALLER TESTS PASSED' -ForegroundColor Green }
