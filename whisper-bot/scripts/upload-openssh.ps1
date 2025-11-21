# Альтернативный способ загрузки через SCP (требуется OpenSSH)
# Запустите в PowerShell из директории проекта

$SERVER = "root@37.233.85.194"
$REMOTE_DIR = "/root/whisper-bot"

Write-Host "🚀 Загрузка файлов на сервер через SCP..." -ForegroundColor Green

# Создание директории на сервере
Write-Host "📁 Создаю директорию на сервере..."
ssh $SERVER "mkdir -p $REMOTE_DIR"

# Загрузка файлов
Write-Host "📤 Загружаю bot.py..."
scp bot.py ${SERVER}:${REMOTE_DIR}/

Write-Host "📤 Загружаю requirements.txt..."
scp requirements.txt ${SERVER}:${REMOTE_DIR}/

Write-Host "📤 Загружаю .env..."
scp .env ${SERVER}:${REMOTE_DIR}/

Write-Host "📤 Загружаю deploy-to-server.sh..."
scp deploy-to-server.sh ${SERVER}:${REMOTE_DIR}/setup.sh

Write-Host ""
Write-Host "✅ Файлы успешно загружены!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Следующий шаг:" -ForegroundColor Yellow
Write-Host "ssh $SERVER"
Write-Host "cd $REMOTE_DIR && chmod +x setup.sh && ./setup.sh"
