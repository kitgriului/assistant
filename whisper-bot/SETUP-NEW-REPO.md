# 🎯 Финальная настройка - Переключение на kitgriului/assistant

## Что нужно сделать на сервере (один раз):

Подключитесь к серверу и выполните команды:

```bash
ssh root@37.233.85.194
# Пароль: atDqr*!ippr2

# Перейдите в директорию бота
cd /root/whisper-bot

# Остановите бота
systemctl stop whisper-bot

# Настройте git для работы с новым репозиторием
git init
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/kitgriului/assistant.git
git config pull.rebase false

# Загрузите код из нового репозитория
git fetch origin
git branch -M main
git reset --hard origin/main

# Загрузите обновленный скрипт update-bot.sh
# (скрипт уже в репозитории, просто делаем его исполняемым)
chmod +x update-bot.sh

# Убедитесь что .env на месте
ls -la .env
# Если .env пустой или отсутствует, создайте его:
# nano .env
# Вставьте ваши токены:
# BOT_TOKEN=your_telegram_bot_token
# OPENAI_API_KEY=your_openai_api_key

# Запустите бота
systemctl start whisper-bot

# Проверьте статус
systemctl status whisper-bot

# Просмотрите логи
journalctl -u whisper-bot -n 20
```

## ✅ Готово!

Теперь при обновлении бота код будет браться из `kitgriului/assistant`!

## 🔄 Использование workflow

### На Windows (для разработки):

```powershell
# 1. Вносите изменения в код
# Редактируете bot.py и другие файлы

# 2. Запускаете скрипт автообновления
.\update-bot-server.ps1
```

Скрипт автоматически:
- ✅ Проверит изменения
- ✅ Закоммитит (если нужно)
- ✅ Отправит в GitHub (kitgriului/assistant)
- ✅ Обновит бота на сервере
- ✅ Перезапустит сервис

### Быстрые команды:

```bash
# Обновление без изменений кода
ssh root@37.233.85.194 "cd /root/whisper-bot && bash update-bot.sh"

# Просмотр логов
ssh root@37.233.85.194 "journalctl -u whisper-bot -f"

# Проверка статуса
ssh root@37.233.85.194 "systemctl status whisper-bot"

# Рестарт бота
ssh root@37.233.85.194 "systemctl restart whisper-bot"
```

## 📍 Ссылки

- **GitHub репозиторий:** https://github.com/kitgriului/assistant
- **Бот в Telegram:** @softmachina_bot
- **Сервер:** 37.233.85.194

## 🚀 Все готово к работе!

Репозиторий переключен на `kitgriului/assistant`. 
Теперь весь workflow будет работать с вашим репозиторием!
