# Python training jarayonini topib, prioritetni "High" ga oshirish
$ErrorActionPreference = 'Continue'

Write-Host ""
Write-Host "Python jarayonlarini topish..." -ForegroundColor Cyan

# Training - Python + GPU/RAM ko'p ishlatadi
$procs = Get-Process python -ErrorAction SilentlyContinue |
         Sort-Object WorkingSet64 -Descending

if (-not $procs) {
    Write-Host "[X] Python jarayoni topilmadi!" -ForegroundColor Red
    Write-Host "    Training ishlamayotgan bo'lishi mumkin." -ForegroundColor Yellow
    exit 1
}

foreach ($p in $procs) {
    $ram = [math]::Round($p.WorkingSet64/1MB, 0)
    $cpu = [math]::Round($p.CPU, 1)
    Write-Host ""
    Write-Host ("PID=" + $p.Id + "  RAM=" + $ram + " MB  CPU=" + $cpu + " sek") -ForegroundColor Yellow
    Write-Host ("  Hozirgi prioritet: " + $p.PriorityClass) -ForegroundColor Gray

    try {
        # High (Realtime emas - Realtime tizimni xanglatishi mumkin)
        $p.PriorityClass = 'High'
        Write-Host ("  [OK] PID " + $p.Id + " - HIGH prioritet o'rnatildi") -ForegroundColor Green
    } catch {
        Write-Host ("  [!] Prioritet o'zgartirilmadi: " + $_.Exception.Message) -ForegroundColor Red
        Write-Host "       (Admin huquq kerak bo'lishi mumkin)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Tugallandi" -ForegroundColor Green
