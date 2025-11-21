# Миграция бота на новую структуру из Git

## Текущая ситуация
- Бот работает на сервере в `/root/whisper-bot`
- Код не в Git репозитории
- Использует старую структуру (`bot.py` в корне)

## Новая структура
- Код в GitHub репозитории `kitgriului/assistant` в папке `whisper-bot`
- Модульная структура с `src/`, `docs/`, `scripts/`
- Точка входа: `src/main.py`

## Шаги миграции

### 1. Подготовка (локально)

Убедитесь, что все изменения запушены в Git:
```powershell
cd C:\Users\User\assistant\whisper-bot
git status
git push origin main
```

### 2. Установка на сервере

Скопируйте скрипт установки на сервер и запустите:

```bash
# Скопировать скрипт на сервер
scp scripts/install-from-git.sh root@37.233.85.194:/tmp/

# Подключиться к серверу
ssh root@37.233.85.194

# Запустить установку
chmod +x /tmp/install-from-git.sh
bash /tmp/install-from-git.sh
```

Скрипт автоматически:
1. Остановит бота
2. Сохранит `.env` файл
3. Создаст backup старой версии
4. Клонирует репозиторий assistant
5. Создаст симлинк `/root/whisper-bot` -> `/root/assistant/whisper-bot`
6. Создаст venv и установит зависимости
7. Обновит systemd сервис
8. Запустит бота

### 3. Обновление в будущем

После миграции для обновления используйте один из скриптов:

**Вариант А: Быстрое обновление (локально)**
```powershell
.\scripts\quick-update.ps1
```

**Вариант Б: Полное обновление с коммитом (локально)**
```powershell
.\scripts\update-bot-server.ps1
```

**Вариант В: На сервере вручную**
```bash
cd /root/whisper-bot
bash scripts/update-bot.sh
```

### 4. Проверка работы

```bash
# Статус бота
systemctl status whisper-bot

# Последние логи
journalctl -u whisper-bot -n 50 --follow
```

## Структура после миграции

```
/root/
├── assistant/                    # Git репозиторий
│   └── whisper-bot/             # Код бота
│       ├── src/                 # Исходный код
│       ├── scripts/             # Скрипты деплоя
│       ├── docs/                # Документация
│       └── .env                 # Конфигурация (не в Git)
└── whisper-bot -> assistant/whisper-bot  # Симлинк для совместимости
```

## Откат при проблемах

Если что-то пошло не так, backup старой версии сохранен:

```bash
# Найти backup
ls -la /root/whisper-bot-backup-*

# Восстановить
systemctl stop whisper-bot
rm -rf /root/whisper-bot
mv /root/whisper-bot-backup-YYYYMMDD-HHMMSS /root/whisper-bot

# Восстановить старый systemd сервис
cat > /etc/systemd/system/whisper-bot.service <<EOF
[Unit]
Description=Whisper Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/whisper-bot
Environment=PATH=/root/whisper-bot/venv/bin
ExecStart=/root/whisper-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=whisper-bot

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl start whisper-bot
```
