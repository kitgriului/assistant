# 🔄 Workflow разработки и обновления бота

## 📋 Как это работает сейчас

### Текущая структура:

```
Локальная разработка (Windows)
         ↓ (git push)
    GitHub Repository
         ↓ (git pull)
   Сервер (37.233.85.194)
         ↓
    Бот работает 24/7
```

---

## 🛠️ Workflow разработки

### 1. Разработка локально (Windows)

```bash
# Работаете с кодом локально
cd c:\Users\User\assistant\whisper-bot

# Редактируете bot.py или другие файлы
# Тестируете локально
python bot.py

# Коммитите изменения
git add .
git commit -m "Описание изменений"
git push origin main
```

### 2. Обновление на сервере

```bash
# Подключаетесь к серверу
ssh root@37.233.85.194

# Переходите в директорию бота
cd /root/whisper-bot

# Останавливаете бота
systemctl stop whisper-bot

# Обновляете код с GitHub
git pull origin main

# Если изменились зависимости - обновляете их
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Перезапускаете бота
systemctl start whisper-bot

# Проверяете статус
systemctl status whisper-bot
```

---

## 🚀 Автоматизация обновлений

Создам скрипты для упрощения процесса:

### Скрипт обновления на сервере: `update-bot.sh`

```bash
#!/bin/bash
# /root/whisper-bot/update-bot.sh

echo "🔄 Обновление Whisper Bot..."

cd /root/whisper-bot

# Останавливаем бота
echo "⏸️  Останавливаю бота..."
systemctl stop whisper-bot

# Сохраняем .env на случай изменений в репозитории
cp .env .env.backup

# Обновляем код
echo "📥 Загружаю изменения с GitHub..."
git pull origin main

# Восстанавливаем .env
mv .env.backup .env

# Обновляем зависимости если нужно
echo "📦 Проверяю зависимости..."
source venv/bin/activate
pip install -r requirements.txt --upgrade --quiet

# Запускаем бота
echo "▶️  Запускаю бота..."
systemctl start whisper-bot

# Ждем запуска
sleep 3

# Проверяем статус
if systemctl is-active --quiet whisper-bot; then
    echo "✅ Бот успешно обновлен и запущен!"
    echo ""
    echo "📊 Статус:"
    systemctl status whisper-bot --no-pager -l
    echo ""
    echo "📋 Последние логи:"
    journalctl -u whisper-bot -n 10 --no-pager
else
    echo "❌ Ошибка! Бот не запустился"
    echo "Просмотрите логи: journalctl -u whisper-bot -n 50"
fi
```

### Скрипт быстрого обновления с Windows: `update-bot-server.bat`

```batch
@echo off
echo ====================================
echo   Обновление бота на сервере
echo ====================================
echo.

echo 1. Проверяем что изменения закоммичены локально...
git status
echo.

echo 2. Отправляем изменения в GitHub...
git push origin main
if errorlevel 1 (
    echo Ошибка при push в GitHub!
    pause
    exit /b 1
)
echo.

echo 3. Подключаемся к серверу и обновляем бота...
ssh root@37.233.85.194 "cd /root/whisper-bot && bash update-bot.sh"

echo.
echo ====================================
echo   Обновление завершено!
echo ====================================
pause
```

### Скрипт быстрого обновления с Windows: `update-bot-server.ps1`

```powershell
# PowerShell версия для более надежной работы

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Обновление бота на сервере" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Проверка что мы в правильной директории
if (-not (Test-Path "bot.py")) {
    Write-Host "Ошибка: bot.py не найден!" -ForegroundColor Red
    Write-Host "Запустите скрипт из директории whisper-bot" -ForegroundColor Red
    exit 1
}

# Проверка статуса git
Write-Host "1. Проверяю статус git..." -ForegroundColor Yellow
git status --short

$changes = git status --porcelain
if ($changes) {
    Write-Host ""
    Write-Host "Обнаружены несохраненные изменения:" -ForegroundColor Yellow
    Write-Host $changes
    Write-Host ""
    $commit = Read-Host "Хотите закоммитить изменения? (y/n)"
    
    if ($commit -eq "y") {
        git add .
        $message = Read-Host "Введите сообщение коммита"
        git commit -m "$message"
    } else {
        Write-Host "Отменено. Сначала закоммитьте изменения." -ForegroundColor Red
        exit 1
    }
}

# Push в GitHub
Write-Host ""
Write-Host "2. Отправляю изменения в GitHub..." -ForegroundColor Yellow
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "Ошибка при push в GitHub!" -ForegroundColor Red
    exit 1
}

# Обновление на сервере
Write-Host ""
Write-Host "3. Подключаюсь к серверу и обновляю бота..." -ForegroundColor Yellow
Write-Host ""

$script = @'
cd /root/whisper-bot && bash update-bot.sh
'@

echo $script | ssh root@37.233.85.194 bash

Write-Host ""
Write-Host "====================================" -ForegroundColor Green
Write-Host "  Обновление завершено!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
```

---

## 📝 Инструкция по использованию

### Первоначальная настройка (один раз):

#### 1. Инициализация Git репозитория (если еще не сделано)

```bash
cd c:\Users\User\assistant\whisper-bot

# Инициализация git
git init

# Добавление удаленного репозитория
git remote add origin https://github.com/otg-tech/bots.git

# Или если используете SSH
git remote add origin git@github.com:otg-tech/bots.git

# Первый коммит
git add .
git commit -m "Initial commit: Whisper bot"
git push -u origin main
```

#### 2. Настройка на сервере

```bash
# Подключаемся к серверу
ssh root@37.233.85.194

# Переходим в директорию бота
cd /root/whisper-bot

# Инициализируем git
git init
git remote add origin https://github.com/otg-tech/bots.git
git fetch origin
git checkout main

# Создаем скрипт обновления
nano update-bot.sh
# Вставляем содержимое скрипта update-bot.sh (см. выше)
# Ctrl+O, Enter, Ctrl+X

# Делаем скрипт исполняемым
chmod +x update-bot.sh
```

---

## 🔄 Ежедневный workflow

### Вариант 1: Автоматический (рекомендуется)

```bash
# На Windows
cd c:\Users\User\assistant\whisper-bot

# Вносите изменения в код
# Редактируете bot.py, добавляете функции и т.д.

# Запускаете скрипт автообновления
.\update-bot-server.ps1
```

Скрипт автоматически:
1. Проверит изменения
2. Предложит закоммитить
3. Отправит в GitHub
4. Обновит и перезапустит бота на сервере

### Вариант 2: Ручной

```bash
# 1. Локально: коммитим и пушим
git add .
git commit -m "Добавил новую функцию"
git push origin main

# 2. На сервере: обновляем
ssh root@37.233.85.194
cd /root/whisper-bot
bash update-bot.sh
```

---

## 🎯 Быстрые команды

### Проверка статуса бота (локально)

```bash
.\check-bot.bat
```

### Просмотр логов

```bash
ssh root@37.233.85.194 "journalctl -u whisper-bot -f"
```

### Быстрый рестарт без обновления

```bash
ssh root@37.233.85.194 "systemctl restart whisper-bot"
```

### Откат к предыдущей версии (на сервере)

```bash
ssh root@37.233.85.194
cd /root/whisper-bot
systemctl stop whisper-bot
git log --oneline  # Смотрим историю
git checkout <commit-hash>  # Откатываемся
systemctl start whisper-bot
```

---

## 🔐 Безопасность .env

⚠️ **Важно:** Файл `.env` с токенами **НЕ ДОЛЖЕН** попадать в GitHub!

Убедитесь что в `.gitignore` есть:

```
.env
.env.local
.env.*.local
```

Скрипт `update-bot.sh` автоматически сохраняет и восстанавливает `.env` при обновлении.

---

## 🐛 Troubleshooting

### Бот не обновляется на сервере

```bash
# Проверьте что изменения есть на GitHub
# Проверьте что на сервере нет конфликтов

ssh root@37.233.85.194
cd /root/whisper-bot
git status
git log --oneline -5
```

### Конфликт при git pull

```bash
# На сервере
cd /root/whisper-bot
git stash  # Сохраняем локальные изменения
git pull origin main
git stash pop  # Восстанавливаем если нужно
```

### Бот не запускается после обновления

```bash
# Проверьте логи
ssh root@37.233.85.194 "journalctl -u whisper-bot -n 50"

# Проверьте что зависимости установлены
ssh root@37.233.85.194 "cd /root/whisper-bot && source venv/bin/activate && pip list"
```

---

## 📚 Полезные ссылки

- **Проверка бота:** `.\check-bot.bat`
- **Обновление бота:** `.\update-bot-server.ps1`
- **Логи на сервере:** `ssh root@37.233.85.194 "journalctl -u whisper-bot -f"`
- **GitHub репозиторий:** https://github.com/otg-tech/bots

---

## 🎓 Лучшие практики

1. **Всегда тестируйте локально** перед деплоем на сервер
2. **Коммитьте часто** с понятными сообщениями
3. **Создавайте ветки** для больших изменений: `git checkout -b feature-name`
4. **Проверяйте логи** после каждого обновления
5. **Делайте бэкапы** .env файла
6. **Документируйте** изменения в коммитах

---

## 🚀 Расширенные возможности

### Автоматическое обновление (webhook)

Можно настроить GitHub Actions для автоматического деплоя при push:

1. Создайте `.github/workflows/deploy.yml`
2. Настройте SSH доступ с GitHub
3. При каждом push бот будет автоматически обновляться

Нужна помощь с настройкой? Дайте знать!
