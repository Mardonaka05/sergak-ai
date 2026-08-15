# Sergak AI - Training jarayonini pauza qiladi (Windows API orqali)
# Ishlatish: powershell -ExecutionPolicy Bypass -File pause_train.ps1

$ErrorActionPreference = 'Stop'

# Win32 API ni yuklash
$code = @"
using System;
using System.Runtime.InteropServices;
public class ProcCtrl {
    [DllImport("ntdll.dll", SetLastError=true)]
    public static extern uint NtSuspendProcess(IntPtr ProcessHandle);
    [DllImport("ntdll.dll", SetLastError=true)]
    public static extern uint NtResumeProcess(IntPtr ProcessHandle);
}
"@
Add-Type -TypeDefinition $code -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Training jarayonini topish..." -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# Training jarayonini topish (Python + RAM ko'p)
$procs = Get-Process python -ErrorAction SilentlyContinue |
         Where-Object { $_.WorkingSet64 -gt 1GB } |
         Sort-Object WorkingSet64 -Descending

if (-not $procs) {
    Write-Host ""
    Write-Host "[X] Training jarayoni topilmadi!" -ForegroundColor Red
    Write-Host "    Training ishlayotganini tekshiring (1+ GB RAM ishlatuvchi Python)" -ForegroundColor Yellow
    Write-Host ""
    Get-Process python -ErrorAction SilentlyContinue |
        Select-Object Id, @{N='RAM_MB';E={[math]::Round($_.WorkingSet64/1MB,0)}}, ProcessName |
        Format-Table -AutoSize
    exit 1
}

foreach ($p in $procs) {
    $ram = [math]::Round($p.WorkingSet64/1MB, 0)
    Write-Host ""
    Write-Host ("Topildi: PID=" + $p.Id + "  RAM=" + $ram + " MB") -ForegroundColor Yellow
    try {
        $result = [ProcCtrl]::NtSuspendProcess($p.Handle)
        if ($result -eq 0) {
            Write-Host ("  [OK] PID " + $p.Id + " - PAUZAGA QO'YILDI") -ForegroundColor Green
        } else {
            Write-Host ("  [X] PID " + $p.Id + " - xato (kod " + $result + ")") -ForegroundColor Red
        }
    } catch {
        Write-Host ("  [X] Xato: " + $_.Exception.Message) -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Endi GPU bo'sh - boshqa ish qila olasiz" -ForegroundColor Green
Write-Host "  Davom ettirish: 12_resume.bat" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
