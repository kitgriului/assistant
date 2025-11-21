# Быстрое руководство: Деплой из Git

## ✅ Проект уже в Git!

Репозиторий: `https://github.com/kitgriului/assistant`
Папка бота: `whisper-bot/`

## 🚀 Обновить бота на сервере (после git push)

### Способ 1: Быстрое обновление (самый простой)
```powershell
.\scripts\quick-update.ps1
```

### Способ 2: С автоматическим коммитом
```powershell
.\scripts\update-bot-server.ps1
```

### Способ 3: На сервере вручную
```bash
cd /root/whisper-bot
bash scripts/update-bot.sh
```

## 📝 Workflow

1. **Вносите изменения локально**
2. **Коммитите и пушите**:
   ```powershell
   git add .
   git commit -m "Описание изменений"
   git push origin main
   ```
3. **Обновляете на сервере**:
   ```powershell
   .\scripts\quick-update.ps1
   ```

## 🔧 Полезные команды

### Проверка статуса бота
```bash
ssh root@37.233.85.194 "systemctl status whisper-bot"
```

### Просмотр логов
```bash
ssh root@37.233.85.194 "journalctl -u whisper-bot -n 50 -f"
```

### Ручной перезапуск
```bash
ssh root@37.233.85.194 "systemctl restart whisper-bot"
```

## ⚠️ Важно

- Файл `.env` НЕ попадает в Git (в `.gitignore`)
- При первом деплое нужно вручную создать `.env` на сервере
- Backup создается автоматически перед каждым обновлением

## 📚 Подробная документация

- [Полная инструкция по миграции](DEPLOY-FROM-GIT.md)
- [Первоначальная установка](DEPLOY-TO-YOUR-SERVER.md)
