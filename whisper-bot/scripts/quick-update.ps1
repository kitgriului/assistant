# Быстрое обновление бота на сервере из Git
# Просто делает git pull на сервере и перезапускает бот

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Быстрое обновление с GitHub" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📥 Обновляю код на сервере..." -ForegroundColor Yellow

ssh root@37.233.85.194 bash -c `"cd /root/assistant/whisper-bot `&`& echo '🔄 Git pull...' `&`& git pull origin main `&`& echo '⏸️  Останавливаю бота...' `&`& systemctl stop whisper-bot `&`& echo '📦 Обновляю зависимости...' `&`& source venv/bin/activate `&`& pip install -r requirements.txt --quiet `&`& echo '▶️  Запускаю бота...' `&`& systemctl start whisper-bot `&`& sleep 3 `&`& if systemctl is-active --quiet whisper-bot`;` then echo '✅ Бот успешно обновлен и запущен!' `&`& systemctl status whisper-bot --no-pager -l | head -10`;` else echo '❌ Ошибка запуска бота!' `&`& journalctl -u whisper-bot -n 20 --no-pager `&`& exit 1`;` fi`"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Обновление завершено успешно!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Произошла ошибка при обновлении" -ForegroundColor Red
    exit 1
}
