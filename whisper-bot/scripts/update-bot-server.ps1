# PowerShell скрипт для автоматического обновления бота на сервере

param(
    [string]$CommitMessage = ""
)

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Обновление бота на сервере" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Проверка что мы в правильной директории
if (-not (Test-Path "src\main.py")) {
    Write-Host "❌ Ошибка: src\main.py не найден!" -ForegroundColor Red
    Write-Host "Запустите скрипт из директории whisper-bot" -ForegroundColor Red
    exit 1
}

# Проверка статуса git
Write-Host "1️⃣  Проверяю статус git..." -ForegroundColor Yellow
$changes = git status --porcelain

if ($changes) {
    Write-Host ""
    Write-Host "📝 Обнаружены несохраненные изменения:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
    
    if (-not $CommitMessage) {
        $commit = Read-Host "Хотите закоммитить изменения? (y/n)"
        
        if ($commit -eq "y") {
            git add .
            $CommitMessage = Read-Host "Введите сообщение коммита"
            git commit -m $CommitMessage
            Write-Host "✅ Изменения закоммичены" -ForegroundColor Green
        } else {
            Write-Host "❌ Отменено. Сначала закоммитьте изменения." -ForegroundColor Red
            exit 1
        }
    } else {
        git add .
        git commit -m $CommitMessage
        Write-Host "✅ Изменения закоммичены: $CommitMessage" -ForegroundColor Green
    }
} else {
    Write-Host "✅ Нет несохраненных изменений" -ForegroundColor Green
}

# Push в GitHub
Write-Host ""
Write-Host "2️⃣  Отправляю изменения в GitHub..." -ForegroundColor Yellow
git push origin main

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при push в GitHub!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Изменения отправлены в GitHub" -ForegroundColor Green

# Обновление на сервере
Write-Host ""
Write-Host "3️⃣  Подключаюсь к серверу и обновляю бота..." -ForegroundColor Yellow
Write-Host ""

$updateScript = @'
cd /root/assistant/whisper-bot && bash scripts/update-bot.sh
'@

$updateScript | ssh root@37.233.85.194 bash

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "====================================" -ForegroundColor Green
    Write-Host "  ✅ Обновление завершено успешно!" -ForegroundColor Green
    Write-Host "====================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎉 Бот обновлен и работает на сервере!" -ForegroundColor Green
    Write-Host "📱 Проверьте бота в Telegram: @softmachina_bot" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "====================================" -ForegroundColor Red
    Write-Host "  ❌ Ошибка при обновлении" -ForegroundColor Red
    Write-Host "====================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Проверьте логи: ssh root@37.233.85.194 'journalctl -u whisper-bot -n 50'" -ForegroundColor Yellow
}
