# 🚀 БЫСТРЫЙ СТАРТ - Деплой GuardBot

## ⚡ Запуск за 3 команды

```bash
# 1. Загрузить код на GitHub
git add .
git commit -m "Ready for production deployment"
git push origin main

# 2. Запустить автодеплой (на Windows используйте Git Bash)
bash deploy.sh

# 3. Создать первого администратора
ssh root@37.233.85.194 'cd /opt/guardbot && docker compose exec guardbot python create_first_admin.py ВАШ_TELEGRAM_ID'
```

**Готово!** Бот запущен и работает. 🎉

---

## 📝 Получить ваш Telegram ID

1. Откройте Telegram
2. Напишите боту: [@userinfobot](https://t.me/userinfobot)
3. Скопируйте ваш ID

---

## 🔄 Обновление бота

### Автоматически (после каждого git push):
```bash
git add .
git commit -m "Update bot"
git push origin main
# GitHub Actions автоматически задеплоит (если настроен)
```

### Вручную (быстрое обновление):
```bash
bash update.sh
```

---

## 📊 Полезные команды

```bash
# Посмотреть логи
ssh root@37.233.85.194 'cd /opt/guardbot && docker compose logs -f'

# Перезапустить бота
ssh root@37.233.85.194 'cd /opt/guardbot && docker compose restart'

# Проверить статус
ssh root@37.233.85.194 'cd /opt/guardbot && docker compose ps'

# Остановить бота
ssh root@37.233.85.194 'cd /opt/guardbot && docker compose down'

# Запустить заново
ssh root@37.233.85.194 'cd /opt/guardbot && docker compose up -d'
```

---

## ⚙️ Что уже настроено

✅ Токен бота: `8213953486:AAGMm7a...`  
✅ GitHub: `git@github.com:otg-tech/bots.git`  
✅ Сервер: `37.233.85.194`  
✅ Docker конфигурация  
✅ Автоматические перезапуски  
✅ Логирование в файл  
✅ Production режим  

---

## 🎯 Первое использование

1. **Запустите деплой:**
   ```bash
   bash deploy.sh
   ```

2. **Создайте администратора:**
   ```bash
   # Замените 123456789 на ваш реальный Telegram ID
   ssh root@37.233.85.194 'cd /opt/guardbot && docker compose exec guardbot python create_first_admin.py 123456789 admin'
   ```

3. **Откройте бота в Telegram:**
   - Найдите вашего бота
   - Отправьте `/start`
   - Должно появиться админ-меню

---

## 🆘 Если что-то пошло не так

### Проблема: "Permission denied"
```bash
# На Windows используйте Git Bash для запуска .sh скриптов
# Или установите WSL (Windows Subsystem for Linux)
```

### Проблема: "Connection refused"
```bash
# Проверьте, что SSH ключ добавлен на сервер
ssh root@37.233.85.194
```

### Проблема: Бот не отвечает
```bash
# Проверьте логи
ssh root@37.233.85.194 'cd /opt/guardbot && docker compose logs --tail=100'
```

---

## 📚 Подробная документация

- [FIRST_DEPLOYMENT.md](FIRST_DEPLOYMENT.md) - Детальная инструкция
- [DEPLOYMENT.md](DEPLOYMENT.md) - Все варианты деплоя
- [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md) - Чеклист готовности

---

**Удачи! Ваш бот готов к работе! 🚀**
