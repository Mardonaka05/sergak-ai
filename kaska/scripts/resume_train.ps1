# Sergak AI - Training jarayonini pauzadan davom ettiradi
# Ishlatish: powershell -ExecutionPolicy Bypass -File resume_train.ps1

$ErrorActionPreference = 'Stop'

$code = @"
using System;
using System.Runtime.InteropServices;
public class ProcCtrl2 {
    [DllImport("ntdll.dll", SetLastError=true)]
    public static extern uint NtResumeProcess(IntPtr ProcessHandle);
}
"@
Add-Type -TypeDefinition $code -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Training jarayonini topish..." -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$procs = Get-Process python -ErrorAction SilentlyContinue |
         Where-Object { $_.WorkingSet64 -gt 1GB } |
         Sort-Object WorkingSet64 -Descending

if (-not $procs) {
    Write-Host ""
    Write-Host "[X] Training jarayoni topilmadi!" -ForegroundColor Red
    exit 1
}

foreach ($p in $procs) {
    $ram = [math]::Round($p.WorkingSet64/1MB, 0)
    Write-Host ""
    Write-Host ("Topildi: PID=" + $p.Id + "  RAM=" + $ram + " MB") -ForegroundColor Yellow
    try {
        $result = [ProcCtrl2]::NtResumeProcess($p.Handle)
        if ($result -eq 0) {
            Write-Host ("  [OK] PID " + $p.Id + " - DAVOM ETMOQDA") -ForegroundColor Green
        } else {
            Write-Host ("  [X] PID " + $p.Id + " - xato (kod " + $result + ")") -ForegroundColor Red
        }
    } catch {
        Write-Host ("  [X] Xato: " + $_.Exception.Message) -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Training davom etmoqda - training oynasiga qarang" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
