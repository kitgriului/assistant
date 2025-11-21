# Загрузка файлов на сервер 37.233.85.194
# Запустите в PowerShell из директории проекта

# Установка plink (если нет)
# winget install PuTTY.PuTTY

# Переменные
$SERVER = "37.233.85.194"
$USER = "root"
$PASSWORD = "atDqr*!ippr2"
$REMOTE_DIR = "/root/whisper-bot"

Write-Host "🚀 Загрузка файлов на сервер..." -ForegroundColor Green

# Создание директории на сервере через SSH
$createDirCmd = "mkdir -p $REMOTE_DIR"
Write-Host "📁 Создаю директорию на сервере..."
echo y | plink -ssh -pw $PASSWORD ${USER}@${SERVER} $createDirCmd

# Загрузка файлов через pscp (PuTTY SCP)
Write-Host "📤 Загружаю bot.py..."
echo y | pscp -pw $PASSWORD bot.py ${USER}@${SERVER}:${REMOTE_DIR}/

Write-Host "📤 Загружаю requirements.txt..."
echo y | pscp -pw $PASSWORD requirements.txt ${USER}@${SERVER}:${REMOTE_DIR}/

Write-Host "📤 Загружаю .env..."
echo y | pscp -pw $PASSWORD .env ${USER}@${SERVER}:${REMOTE_DIR}/

Write-Host ""
Write-Host "✅ Файлы успешно загружены!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Следующие шаги:" -ForegroundColor Yellow
Write-Host "1. Подключитесь к серверу: ssh root@37.233.85.194"
Write-Host "2. Запустите установку: cd /root/whisper-bot && bash setup.sh"
