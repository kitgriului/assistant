# Обновление systemd сервиса на сервере
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Обновление systemd сервиса" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Копирую файл сервиса на сервер..." -ForegroundColor Yellow
scp scripts/whisper-bot.service root@37.233.85.194:/etc/systemd/system/

if ($LASTEXITCODE -ne 0) {
    Write-Host "Ошибка при копировании файла!" -ForegroundColor Red
    exit 1
}

Write-Host "Файл скопирован" -ForegroundColor Green
Write-Host ""

Write-Host "2. Перезагружаю systemd и перезапускаю бота..." -ForegroundColor Yellow

ssh root@37.233.85.194 "systemctl daemon-reload && systemctl restart whisper-bot"

if ($LASTEXITCODE -eq 0) {
    Start-Sleep -Seconds 3
    Write-Host ""
    Write-Host "3. Проверяю статус бота..." -ForegroundColor Yellow
    ssh root@37.233.85.194 "systemctl status whisper-bot --no-pager -l | head -15"
    
    Write-Host ""
    Write-Host "Systemd сервис обновлен успешно!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Произошла ошибка" -ForegroundColor Red
    exit 1
}
