# Быстрое обновление бота на сервере из Git
# Просто делает git pull на сервере и перезапускает бот

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Быстрое обновление с GitHub" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📥 Обновляю код на сервере..." -ForegroundColor Yellow

ssh root@37.233.85.194 "cd /root/whisper-bot && bash scripts/update-bot.sh"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Обновление завершено успешно!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Произошла ошибка при обновлении" -ForegroundColor Red
    exit 1
}
