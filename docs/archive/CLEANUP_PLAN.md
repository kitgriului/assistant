# План очистки проекта

## Дата: 2025-01-11
## Цель: Подготовка проекта к продакшену

### 1. Избыточные скрипты (переместить в `_deprecated/`)

#### Утилиты администрирования (11 файлов):
- `add_users_direct.py` - Прямое добавление пользователей
- `create_admin.py` - Создание админа
- `make_admin.py` - Назначение админа
- `set_admin.py` - Установка админа (дубликат)
- `init_users.py` - Инициализация пользователей
- `setup_users.py` - Настройка пользователей
- `create_new_request.py` - Создание тестовой заявки
- `add_indexes.py` - Добавление индексов (уже применено)
- `migrate_db.py` - Миграция БД (разовая операция)
- `quick_reset.py` - Быстрый сброс данных
- `reset_bot.py` - Полный сброс бота

#### Диагностические скрипты (7 файлов):
- `check_data.py` - Проверка данных
- `check_db.py` - Проверка БД
- `check_qr.py` - Проверка QR-кодов
- `debug_approve.py` - Отладка одобрения
- `fix_webhook.py` - Исправление вебхука
- `generate_test_qr.py` - Генерация тестовых QR
- `test_qr_data.py` - Тестирование QR-данных

#### Тестовые скрипты (4 файла):
- `test_approve.py` - Тест одобрения
- `test_auth.py` - Тест авторизации
- `test_photo_flow.py` - Тест загрузки фото
- `TEST_NEW_AUTH.md` - Тестовая документация

### 2. Избыточная документация (консолидировать в `docs/`)

#### Отчеты о рефакторинге (6 файлов - архивировать):
- `REFACTORING_REPORT.md` - Старый отчет
- `REFACTORING_REPORT_2025.md` - Отчет 2025
- `REFACTORING_SUMMARY.md` - Сводка рефакторинга
- `REFACTORING_PLAN.md` - План рефакторинга v1
- `REFACTORING_PLAN_V2.md` - План рефакторинга v2
- `REFACTORING_CHECKLIST.md` - Чеклист рефакторинга
- `STAGE1_REPORT.md` - Отчет этапа 1
- `BUGFIXES_CHANGELOG.md` - Лог исправлений

#### README файлы (4 файла - объединить):
- `README.md` - Основной README
- `README_NEW.md` - Новый README
- `QUICK_START.md` - Быстрый старт
- `INSTALLATION_GUIDE.md` - Руководство по установке

#### Технические документы (сохранить в `docs/`):
- `TECHNICAL.md` - Техническая документация
- `TECHNICAL_SUPPLEMENT.md` - Дополнение
- `REQUEST_FLOW.md` - Поток заявок
- `PATROL_GUIDE.md` - Руководство по обходам
- `PATROL_UX_GUIDE.md` - UX обходов
- `NOTIFICATIONS.md` - Уведомления
- `FAQ.md` - FAQ
- `TEST_GUIDE.md` - Руководство по тестированию
- `SETUP_GUIDE.md` - Руководство по настройке
- `USAGE_GUIDE.md` - Руководство пользователя

#### Планы развития (сохранить в `docs/roadmap/`):
- `ROADMAP.md` - Дорожная карта
- `STATUS.md` - Текущий статус
- `DIAGNOSIS.md` - Диагностика
- `CHANGELOG.md` - История изменений

### 3. Дублирующиеся файлы
- `test_guardbot.db` - Тестовая БД (удалить)
- `reset_output.txt` - Вывод сброса (удалить)
- `.DS_Store` - macOS файл (удалить)

### 4. Предлагаемая структура

```
guardbot/
├── README.md                      # Основной README (объединенный)
├── requirements.txt
├── Dockerfile
├── .env.example
├── .gitignore
├── run_bot.py                     # Главный запускающий скрипт
├── version.txt
├── guardbot.db                    # Продакшн БД
│
├── bot/                           # Основной код бота
│   ├── config.py
│   └── main.py
│
├── database/                      # Модели БД
│   ├── __init__.py
│   ├── models.py
│   └── session.py
│
├── handlers/                      # Обработчики команд
│   ├── __init__.py
│   ├── admin.py
│   ├── applicant.py
│   ├── auth.py
│   ├── auth_phone.py
│   ├── client.py
│   ├── guard.py
│   ├── menu.py
│   ├── patrol.py
│   └── requests.py
│
├── states/                        # FSM состояния
│   ├── __init__.py
│   ├── applicant.py
│   ├── auth.py
│   ├── client.py
│   └── guard.py
│
├── utils/                         # Утилиты
│   ├── __init__.py
│   ├── auth.py
│   ├── build.py
│   ├── calendar_kb.py
│   ├── constants.py
│   ├── export.py
│   ├── media.py
│   ├── qr.py
│   ├── roles.py
│   └── user_helpers.py
│
├── data/                          # Данные приложения
│   ├── export/
│   └── media/
│
├── tests/                         # Тесты
│   ├── test_db.py
│   └── test_qr.py
│
├── docs/                          # **НОВАЯ** Документация
│   ├── user/
│   │   ├── quick-start.md
│   │   ├── installation.md
│   │   ├── usage-guide.md
│   │   └── faq.md
│   ├── technical/
│   │   ├── architecture.md
│   │   ├── database.md
│   │   ├── request-flow.md
│   │   └── patrol-system.md
│   ├── guides/
│   │   ├── patrol-guide.md
│   │   ├── setup-guide.md
│   │   └── test-guide.md
│   ├── roadmap/
│   │   ├── roadmap.md
│   │   ├── status.md
│   │   └── changelog.md
│   └── archive/
│       └── refactoring-reports/
│
└── _deprecated/                   # **НОВАЯ** Устаревшие скрипты
    ├── admin/
    ├── diagnostics/
    └── tests/
```

### 5. Приоритеты выполнения

**Фаза 1: Подготовка (текущая)**
1. ✅ Создать план очистки
2. ⏳ Создать структуру папок (`docs/`, `_deprecated/`)
3. ⏳ Переместить скрипты в `_deprecated/`
4. ⏳ Организовать документацию в `docs/`

**Фаза 2: Консолидация**
1. Объединить README файлы
2. Архивировать отчеты о рефакторинге
3. Удалить дублирующиеся файлы

**Фаза 3: Финализация**
1. Обновить основной README
2. Создать CONTRIBUTING.md
3. Обновить .gitignore

### 6. Критерии успеха
- ✅ Корневая директория содержит не более 15 файлов
- ✅ Вся документация в `docs/`
- ✅ Все утилиты в `_deprecated/` с README
- ✅ Понятная структура для новых разработчиков
- ✅ Сохранены все исторические данные
